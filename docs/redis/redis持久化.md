![image-20220126150523962](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202201261505024.png)

## 写在前面

> 本文从整体上详细介绍Redis的两种持久化方式，包含工作原理、持久化流程及实践策略，以及背后的一些理论知识。上一篇文章仅介绍了RDB持久化，但是Redis持久化是一个整体，单独介绍不成体系，故重新整理。

Redis是一个内存数据库，所有的数据将保存在内存中，这与传统的MySQL、Oracle、SqlServer等关系型数据库直接把数据保存到硬盘相比，Redis的读写效率非常高。但是保存在内存中也有一个很大的缺陷，一旦断电或者宕机，内存数据库中的内容将会全部丢失。为了弥补这一缺陷，Redis提供了把内存数据持久化到硬盘文件，以及通过备份文件来恢复数据的功能，即Redis持久化机制。

Redis支持两种方式的持久化：RDB快照和AOF。

## RDB持久化

RDB快照用官方的话来说：RDB持久化方案是按照指定时间间隔对你的数据集生成的时间点快照（point-to-time
snapshot）。它以紧缩的二进制文件保存Redis数据库某一时刻所有数据对象的内存快照，可用于Redis的数据备份、转移与恢复。到目前为止，仍是官方的默认支持方案。

### RDB工作原理

既然说RDB是Redis中数据集的时间点快照，那我们先简单了解一下Redis内的数据对象在内存中是如何存储与组织的。

默认情况下，Redis中有16个数据库，编号从0-15，每个Redis数据库使用一个`redisDb`对象来表示，`redisDb`
使用hashtable存储K-V对象。为方便理解，我以其中一个db为例绘制Redis内部数据的存储结构示意图。
![image-20220126150613336](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202201261506368.png)

时间点快照也就是某一时刻Redis内每个DB中每个数据对象的状态，**先假设在这一时刻所有的数据对象不再改变**
，我们就可以按照上图中的数据结构关系，把这些数据对象依次读取出来并写入到文件中，以此实现Redis的持久化。然后，当Redis重启时按照规则读取这个文件中的内容，再写入到Redis内存即可恢复至持久化时的状态。

当然，这个前提时我们上面的假设成立，否则面对一个时刻变化的数据集，我们无从下手。我们知道Redis中客户端命令处理是单线程模型，如果把持久化作为一个命令处理，那数据集肯定时处于静止状态。另外，操作系统提供的fork()
函数创建的子进程可获得与父进程一致的内存数据，相当于获取了内存数据副本；fork完成后，父进程该干嘛干嘛，持久化状态的工作交给子进程就行了。

很显然，第一种情况不可取，持久化备份会导致短时间内Redis服务不可用，这对于高HA的系统来讲是无法容忍的。所以，第二种方式是RDB持久化的主要实践方式。由于fork子进程后，父进程数据一直在变化，子进程并不与父进程同步，RDB持久化必然无法保证实时性；RDB持久化完成后发生断电或宕机，会导致部分数据丢失；备份频率决定了丢失数据量的大小，提高备份频率，意味着fork过程消耗较多的CPU资源，也会导致较大的磁盘I/O。

### 持久化流程

在Redis内完成RDB持久化的方法有rdbSave和rdbSaveBackground两个函数方法（源码文件rdb.c中），先简单说下两者差别：

- rdbSave：是同步执行的，方法调用后就会立刻启动持久化流程。由于Redis是单线程模型，持久化过程中会阻塞，Redis无法对外提供服务；
- rdbSaveBackground：是后台（异步）执行的，该方法会fork出子进程，真正的持久化过程是在子进程中执行的（调用rdbSave），主进程会继续提供服务；

RDB持久化的触发必然离不开以上两个方法，触发的方式分为手动和自动。手动触发容易理解，是指我们通过Redis客户端人为的对Redis服务端发起持久化备份指令，然后Redis服务端开始执行持久化流程，这里的指令有save和bgsave。自动触发是Redis根据自身运行要求，在满足预设条件时自动触发的持久化流程，自动触发的场景有如下几个（[摘自这篇文章](https://link.segmentfault.com/?enc=XtlP5wm2CXDfKybJvwmwvQ%3D%3D.C6me7DGkNlqREBa%2BUujT0p6ZtXRgoOrghiOiNmCdIF34AmGYo9Qq9bImWZBrBB37)）：

- serverCron中`save m n`配置规则自动触发；
- 从节点全量复制时，主节点发送rdb文件给从节点完成复制操作，主节点会出发bgsave；
- 执行`debug reload`命令重新加载redis时；
- 默认情况下（未开启AOF）执行shutdown命令时，自动执行bgsave；

结合源码及参考文章，我整理了RDB持久化流程来帮助大家有个整体的了解，然后再从一些细节进行说明。
![image-20220126150646727](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202201261506755.png)

s从上图可以知道：

- 自动触发的RDB持久化是通过rdbSaveBackground以子进程方式执行的持久化策略；
- 手动触发是以客户端命令方式触发的，包含save和bgsave两个命令，其中save命令是在Redis的命令处理线程以阻塞的方式调用`rdbSave`方法完成的。

自动触发流程是一个完整的链路，涵盖了rdbSaveBackground、rdbSave等，接下来我以serverCron为例分析一下整个流程。

#### save规则及检查

serverCron是Redis内的一个周期性函数，每隔100毫秒执行一次，它的其中一项工作就是：根据配置文件中save规则来判断当前需要进行自动持久化流程，如果满足条件则尝试开始持久化。了解一下这部分的实现。

在`redisServer`中有几个与RDB持久化有关的字段，我从代码中摘出来，中英文对照着看下：

```c
struct redisServer {
    /* 省略其他字段 */ 
    /* RDB persistence */
    long long dirty;                /* Changes to DB from the last save
                                     * 上次持久化后修改key的次数 */
    struct saveparam *saveparams;   /* Save points array for RDB，
                                     * 对应配置文件多个save参数 */
    int saveparamslen;              /* Number of saving points，
                                     * save参数的数量 */
    time_t lastsave;                /* Unix time of last successful save 
                                     * 上次持久化时间*/
    /* 省略其他字段 */
}

/* 对应redis.conf中的save参数 */
struct saveparam {
    time_t seconds;                    /* 统计时间范围 */   
    int changes;                    /* 数据修改次数 */
};
```

`saveparams`对应`redis.conf`下的save规则，save参数是Redis触发自动备份的触发策略，`seconds`为统计时间（单位：秒）， `changes`为在统计时间内发生写入的次数。`save m n`
的意思是：m秒内有n条写入就触发一次快照，即备份一次。save参数可以配置多组，满足在不同条件的备份要求。如果需要关闭RDB的自动备份策略，可以使用`save ""`。以下为几种配置的说明：

```shell
# 表示900秒（15分钟）内至少有1个key的值发生变化，则执行
save 900 1
# 表示300秒（5分钟）内至少有1个key的值发生变化，则执行
save 300 10
# 表示60秒（1分钟）内至少有10000个key的值发生变化，则执行
save 60 10000
# 该配置将会关闭RDB方式的持久化
save ""
```

`serverCron`对RDB save规则的检测代码如下所示：

```c
int serverCron(struct aeEventLoop *eventLoop, long long id, void *clientData) {
    /* 省略其他逻辑 */
    
    /* 如果用户请求进行AOF文件重写时，Redis正在执行RDB持久化，Redis会安排在RDB持久化完成后执行AOF文件重写，
     * 如果aof_rewrite_scheduled为true，说明需要执行用户的请求 */
    /* Check if a background saving or AOF rewrite in progress terminated. */
    if (hasActiveChildProcess() || ldbPendingChildren())
    {
        run_with_period(1000) receiveChildInfo();
        checkChildrenDone();
    } else {
        /* 后台无 saving/rewrite 子进程才会进行，逐个检查每个save规则*/
        for (j = 0; j < server.saveparamslen; j++) {
            struct saveparam *sp = server.saveparams+j;
            
            /* 检查规则有几个：满足修改次数，满足统计周期，达到重试时间间隔或者上次持久化完成*/
            if (server.dirty >= sp->changes 
                && server.unixtime-server.lastsave > sp->seconds 
                &&(server.unixtime-server.lastbgsave_try > CONFIG_BGSAVE_RETRY_DELAY || server.lastbgsave_status == C_OK))
            {
                serverLog(LL_NOTICE,"%d changes in %d seconds. Saving...", sp->changes, (int)sp->seconds);
                rdbSaveInfo rsi, *rsiptr;
                rsiptr = rdbPopulateSaveInfo(&rsi);
                /* 执行bgsave过程 */
                rdbSaveBackground(server.rdb_filename,rsiptr);
                break;
            }
        }

        /* 省略：Trigger an AOF rewrite if needed. */
    }
    /* 省略其他逻辑 */
}
```

如果没有后台的RDB持久化或AOF重写进程，serverCron会根据以上配置及状态判断是否需要执行持久化操作，判断依据就是看lastsave、dirty是否满足saveparams数组中的其中一个条件。如果有一个条件匹配，则调用rdbSaveBackground方法，执行异步持久化流程。

#### rdbSaveBackground

rdbSaveBackground是RDB持久化的辅助性方法，主要工作是fork子进程，然后根据调用方（父进程或者子进程）不同，有两种不同的执行逻辑。

- 如果调用方是父进程，则fork出子进程，保存子进程信息后直接返回。
- 如果调用方是子进程则调用rdbSave执行RDB持久化逻辑，持久化完成后退出子进程。

```c
int rdbSaveBackground(char *filename, rdbSaveInfo *rsi) {
    pid_t childpid;

    if (hasActiveChildProcess()) return C_ERR;

    server.dirty_before_bgsave = server.dirty;
    server.lastbgsave_try = time(NULL);

    // fork子进程
    if ((childpid = redisFork(CHILD_TYPE_RDB)) == 0) {
        int retval;

        /* Child 子进程：修改进程标题 */
        redisSetProcTitle("redis-rdb-bgsave");
        redisSetCpuAffinity(server.bgsave_cpulist);
        // 执行rdb持久化
        retval = rdbSave(filename,rsi);
        if (retval == C_OK) {
            sendChildCOWInfo(CHILD_TYPE_RDB, 1, "RDB");
        }
        // 持久化完成后，退出子进程
        exitFromChild((retval == C_OK) ? 0 : 1);
    } else {
        /* Parent 父进程：记录fork子进程的时间等信息*/
        if (childpid == -1) {
            server.lastbgsave_status = C_ERR;
            serverLog(LL_WARNING,"Can't save in background: fork: %s",
                strerror(errno));
            return C_ERR;
        }
        serverLog(LL_NOTICE,"Background saving started by pid %ld",(long) childpid);
        // 记录子进程开始的时间、类型等。
        server.rdb_save_time_start = time(NULL);
        server.rdb_child_type = RDB_CHILD_TYPE_DISK;
        return C_OK;
    }
    return C_OK; /* unreached */
}
```

rdbSave是真正执行持久化的方法，它在执行时存在大量的I/O、计算操作，耗时、CPU占用较大，在Redis的单线程模型中持久化过程会持续占用线程资源，进而导致Redis无法提供其他服务。为了解决这一问题Redis在rdbSaveBackground中fork出子进程，由子进程完成持久化工作，避免了占用父进程过多的资源。

需要注意的是，如果父进程内存占用过大，fork过程会比较耗时，在这个过程中父进程无法对外提供服务；另外，需要综合考虑计算机内存使用量，fork子进程后会占用双倍的内存资源，需要确保内存够用。通过info
stats命令查看latest_fork_usec选项，可以获取最近一个fork以操作的耗时。

#### rdbSave

Redis的rdbSave函数是真正进行RDB持久化的函数，流程、细节贼多，整体流程可以总结为：创建并打开临时文件、Redis内存数据写入临时文件、临时文件写入磁盘、临时文件重命名为正式RDB文件、更新持久化状态信息（dirty、lastsave）。其中“Redis内存数据写入临时文件”最为核心和复杂，写入过程直接体现了RDB文件的文件格式，本着一图胜千言的理念，我按照源码流程绘制了下图。
![image-20220126150742208](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202201261507237.png)

补充说明一下，上图右下角“遍历当前数据库的键值对并写入”这个环节会根据不同类型的Redis数据类型及底层数据结构采用不同的格式写入到RDB文件中，不再展开了。我觉得大家对整个过程有个直观的理解就好，这对于我们理解Redis内部的运作机制大有裨益。

### AOF持久化

上一节我们知道RDB是一种时间点（point-to-time）快照，适合数据备份及灾难恢复，由于工作原理的“先天性缺陷”无法保证实时性持久化，这对于缓存丢失零容忍的系统来说是个硬伤，于是就有了AOF。

### AOF工作原理

AOF是Append Only File的缩写，它是Redis的完全持久化策略，从1.1版本开始支持；这里的file存储的是引起Redis数据修改的命令集合（比如：set/hset/del等），这些集合按照Redis
Server的处理顺序追加到文件中。当重启Redis时，Redis就可以从头读取AOF中的指令并重放，进而恢复关闭前的数据状态。

AOF持久化默认是关闭的，修改redis.conf以下信息并重启，即可开启AOF持久化功能。

```gams
# no-关闭，yes-开启，默认no
appendonly yes
appendfilename appendonly.aof
```

AOF本质是为了持久化，持久化对象是Redis内每一个key的状态，持久化的目的是为了在Reids发生故障重启后能够恢复至重启前或故障前的状态。相比于RDB，AOF采取的策略是按照执行顺序持久化每一条能够引起Redis中对象状态变更的命令，命令是有序的、有选择的。把aof文件转移至任何一台Redis
Server，从头到尾按序重放这些命令即可恢复如初。举个例子：

首先执行指令`set number 0`，然后随机调用`incr number`、`get number` 各5次，最后再执行一次`get number` ，我们得到的结果肯定是5。

因为在这个过程中，能够引起`number`状态变更的只有`set/incr`类型的指令，并且它们执行的先后顺序是已知的，无论执行多少次`get`都不会影响`number`的状态。所以，保留所有`set/incr`
命令并持久化至aof文件即可。按照aof的设计原理，aof文件中的内容应该是这样的（这里是假设，实际为RESP协议）：

```shell
set number 0
incr number
incr number
incr number
incr number
incr number
```

最本质的原理用“命令重放”四个字就可以概括。但是，考虑实际生产环境的复杂性及操作系统等方面的限制，Redis所要考虑的工作要比这个例子复杂的多：

- Redis
  Server启动后，aof文件一直在追加命令，文件会越来越大。文件越大，Redis重启后恢复耗时越久；文件太大，转移工作就越难；不加管理，可能撑爆硬盘。很显然，需要在合适的时机对文件进行精简。例子中的5条incr指令很明显的可以替换为为一条`set`
  命令，存在很大的压缩空间。
- 众所周知，文件I/O是操作系统性能的短板，为了提高效率，文件系统设计了一套复杂的缓存机制，Redis操作命令的追加操作只是把数据写入了缓冲区（aof_buf），从缓冲区到写入物理文件在性能与安全之间权衡会有不同的选择。
- 文件压缩即意味着重写，重写时即可依据已有的aof文件做命令整合，也可以先根据当前Redis内数据的状态做快照，再把存储快照过程中的新增的命令做追加。
- aof备份后的文件是为了恢复数据，结合aof文件的格式、完整性等因素，Redis也要设计一套完整的方案做支持。

### 持久化流程

从流程上来看，AOF的工作原理可以概括为几个步骤：命令追加（append）、文件写入与同步（fsync）、文件重写（rewrite）、重启加载（load），接下来依次了解每个步骤的细节及背后的设计哲学。
![image-20220126150809032](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202201261508058.png)

#### 命令追加

当 AOF 持久化功能处于打开状态时，Redis 在执行完一个写命令之后，会以协议格式(也就是RESP，即 Redis 客户端和服务器交互的通信协议 )把被执行的写命令追加到 Redis 服务端维护的 AOF
缓冲区末尾。对AOF文件只有单线程的追加操作，没有seek等复杂的操作，即使断电或宕机也不存在文件损坏风险。另外，使用文本协议好处多多：

- 文本协议有很好的兼容性；
- 文本协议就是客户端的请求命令，不需要二次处理，节省了存储及加载时的处理开销；
- 文本协议具有可读性，方便查看、修改等处理。

AOF缓冲区类型为Redis自主设计的数据结构`sds`，Redis会根据命令的类型采用不同的方法（`catAppendOnlyGenericCommand`、`catAppendOnlyExpireAtCommand`
等）对命令内容进行处理，最后写入缓冲区。

需要注意的是：如果命令追加时正在进行AOF重写，这些命令还会追加到重写缓冲区（`aof_rewrite_buffer`）。

#### 文件写入与同步

AOF文件的写入与同步离不开操作系统的支持，开始介绍之前，我们需要补充一下Linux
I/O缓冲区相关知识。硬盘I/O性能较差，文件读写速度远远比不上CPU的处理速度，如果每次文件写入都等待数据写入硬盘，会整体拉低操作系统的性能。为了解决这个问题，操作系统提供了延迟写（delayed write）机制来提高硬盘的I/O性能。
![image-20220126150828356](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202201261508384.png)

> 传统的UNIX实现在内核中设有缓冲区高速缓存或页面高速缓存，大多数磁盘I/O都通过缓冲进行。 当将数据写入文件时，内核通常先将该数据复制到其中一个缓冲区中，如果该缓冲区尚未写满，则并不将其排入输出队列，而是等待其写满或者当内核需要重用该缓冲区以便存放其他磁盘块数据时， 再将该缓冲排入到输出队列，然后待其到达队首时，才进行实际的I/O操作。这种输出方式就被称为延迟写。

延迟写减少了磁盘读写次数，但是却降低了文件内容的更新速度，使得欲写到文件中的数据在一段时间内并没有写到磁盘上。当系统发生故障时，这种延迟可能造成文件更新内容的丢失。为了保证磁盘上实际文件系统与缓冲区高速缓存中内容的一致性，UNIX系统提供了sync、fsync和fdatasync三个函数为强制写入硬盘提供支持。

Redis每次事件轮训结束前（`beforeSleep`）都会调用函数`flushAppendOnlyFile`，`flushAppendOnlyFile`会把AOF缓冲区（`aof_buf`
）中的数据写入内核缓冲区，并且根据`appendfsync`配置来决定采用何种策略把内核缓冲区中的数据写入磁盘，即调用`fsync()`。该配置有三个可选项`always`、`no`、`everysec`，具体说明如下：

- always：每次都调用`fsync()`，是安全性最高、性能最差的一种策略。
- no：不会调用`fsync()`。性能最好，安全性最差。
- everysec：仅在满足同步条件时调用`fsync()`。这是官方建议的同步策略，也是默认配置，做到兼顾性能和数据安全性，理论上只有在系统突然宕机的情况下丢失1秒的数据。

**注意：上面介绍的策略受配置项`no-appendfsync-on-rewrite`的影响，它的作用是告知Redis：AOF文件重写期间是否禁止调用fsync()，默认是no。**

如果`appendfsync`设置为`always`或`everysec`，后台正在进行的`BGSAVE`或者`BGREWRITEAOF`消耗过多的磁盘I/O，在某些Linux系统配置下，Redis对fsync()
的调用可能阻塞很长时间。然而这个问题还没有修复，因为即使是在不同的线程中执行`fsync()`，同步写入操作也会被阻塞。

为了缓解此问题，可以使用该选项，以防止在进行`BGSAVE`或`BGREWRITEAOF`时在主进程中调用fsync(）。

- 设置为`yes`意味着，如果子进程正在进行`BGSAVE`或`BGREWRITEAOF`，AOF的持久化能力就与`appendfsync`设置为`no`有着相同的效果。最糟糕的情况下，这可能会导致30秒的缓存数据丢失。
- 如果你的系统有上面描述的延迟问题，就把这个选项设置为`yes`，否则保持为`no`。

#### 文件重写

如前面提到的，Redis长时间运行，命令不断写入AOF，文件会越来越大，不加控制可能影响宿主机的安全。

为了解决AOF文件体积问题，Redis引入了AOF文件重写功能，它会根据Redis内数据对象的最新状态生成新的AOF文件，新旧文件对应的数据状态一致，但是新文件会具有较小的体积。重写既减少了AOF文件对磁盘空间的占用，又可以提高Redis重启时数据恢复的速度。还是下面这个例子，旧文件中的6条命令等同于新文件中的1条命令，压缩效果显而易见。
![image-20220126150845435](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202201261508465.png)

**我们说，AOF文件太大时会触发AOF文件重写，那到底是多大呢？有哪些情况会触发重写操作呢？**
**
与RDB方式一样，AOF文件重写既可以手动触发，也会自动触发。手动触发直接调用`bgrewriteaof`命令，如果当时无子进程执行会立刻执行，否则安排在子进程结束后执行。自动触发由Redis的周期性方法`serverCron`
检查在满足一定条件时触发。先了解两个配置项：

- auto-aof-rewrite-percentage：代表当前AOF文件大小（aof_current_size）和上一次重写后AOF文件大小（aof_base_size）相比，增长的比例。
- auto-aof-rewrite-min-size：表示运行`BGREWRITEAOF`时AOF文件占用空间最小值，默认为64MB；

Redis启动时把`aof_base_size`初始化为当时aof文件的大小，Redis运行过程中，当AOF文件重写操作完成时，会对其进行更新；`aof_current_size`为`serverCron`
执行时AOF文件的实时大小。当满足以下两个条件时，AOF文件重写就会触发：

```arduino
增长比例：(aof_current_size - aof_base_size) / aof_base_size > auto-aof-rewrite-percentage
文件大小：aof_current_size > auto-aof-rewrite-min-size
```

手动触发与自动触发的代码如下，同样在周期性方法`serverCron`中：

```c
int serverCron(struct aeEventLoop *eventLoop, long long id, void *clientData) {
    /* 省略其他逻辑 */
    
    /* 如果用户请求进行AOF文件重写时，Redis正在执行RDB持久化，Redis会安排在RDB持久化完成后执行AOF文件重写，
     * 如果aof_rewrite_scheduled为true，说明需要执行用户的请求 */
    if (!hasActiveChildProcess() &&
        server.aof_rewrite_scheduled)
    {
        rewriteAppendOnlyFileBackground();
    }

    /* Check if a background saving or AOF rewrite in progress terminated. */
    if (hasActiveChildProcess() || ldbPendingChildren())
    {
        run_with_period(1000) receiveChildInfo();
        checkChildrenDone();
    } else {
        /* 省略rdb持久化条件检查 */

        /* AOF重写条件检查：aof开启、无子进程运行、增长百分比已设置、当前文件大小超过阈值 */
        if (server.aof_state == AOF_ON &&
            !hasActiveChildProcess() &&
            server.aof_rewrite_perc &&
            server.aof_current_size > server.aof_rewrite_min_size)
        {
            long long base = server.aof_rewrite_base_size ?
                server.aof_rewrite_base_size : 1;
            /* 计算增长百分比 */
            long long growth = (server.aof_current_size*100/base) - 100;
            if (growth >= server.aof_rewrite_perc) {
                serverLog(LL_NOTICE,"Starting automatic rewriting of AOF on %lld%% growth",growth);
                rewriteAppendOnlyFileBackground();
            }
        }
    }
    /**/
}
```

**AOF文件重写的流程是什么？听说Redis支持混合持久化，对AOF文件重写有什么影响？**

从4.0版本开始，Redis在AOF模式中引入了混合持久化方案，即：纯AOF方式、RDB+AOF方式，这一策略由配置参数`aof-use-rdb-preamble`（使用RDB作为AOF文件的前半段）控制，默认关闭(no)
，设置为yes可开启。所以，在AOF重写过程中文件的写入会有两种不同的方式。当`aof-use-rdb-preamble`的值是：

- no：按照AOF格式写入命令，与4.0前版本无差别；
- yes：先按照RDB格式写入数据状态，然后把重写期间AOF缓冲区的内容以AOF格式写入，文件前半部分为RDB格式，后半部分为AOF格式。

结合源码（6.0版本，源码太多这里不贴出，可参考`aof.c`）及参考资料，绘制AOF重写（BGREWRITEAOF）流程图：

![image-20220126150911849](/Users/jiaxiansheng/Library/Application%20Support/typora-user-images/image-20220126150911849.png)

结合上图，总结一下AOF文件重写的流程：

- rewriteAppendOnlyFileBackground开始执行，检查是否有正在进行的AOF重写或RDB持久化子进程：如果有，则退出该流程；如果没有，则继续创建接下来父子进程间数据传输的通信管道。执行fork()
  操作，成功后父子进程分别执行不同的流程。
- 父进程：
    - 记录子进程信息（pid）、时间戳等；
    - 继续响应其他客户端请求；
    - 收集AOF重写期间的命令，追加至aof_rewrite_buffer；
    - 等待并向子进程同步aof_rewrite_buffer的内容；
- 子进程：
    - 修改当前进程名称，创建重写所需的临时文件，调用rewriteAppendOnlyFile函数；
    - 根据`aof-use-rdb-preamble`配置，以RDB或AOF方式写入前半部分，并同步至硬盘；
    - 从父进程接收增量AOF命令，以AOF方式写入后半部分，并同步至硬盘；
    - 重命名AOF文件，子进程退出。

## 数据加载

Redis启动后通过`loadDataFromDisk`函数执行数据加载工作。这里需要注意，虽然持久化方式可以选择AOF、RDB或者两者兼用，但是数据加载时必须做出选择，两种方式各自加载一遍就乱套了。

理论上，AOF持久化比RDB具有更好的实时性，当开启了AOF持久化方式，Redis在数据加载时优先考虑AOF方式。而且，Redis 4.0版本后AOF支持了混合持久化，加载AOF文件需要考虑版本兼容性。Redis数据加载流程如下图所示：
![image-20220126150935280](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202201261509317.png)

在AOF方式下，开启混合持久化机制生成的文件是“RDB头+AOF尾”，未开启时生成的文件全部为AOF格式。考虑两种文件格式的兼容性，如果Redis发现AOF文件为RDB头，会使用RDB数据加载的方法读取并恢复前半部分；然后再使用AOF方式读取并恢复后半部分。由于AOF格式存储的数据为RESP协议命令，Redis采用伪客户端执行命令的方式来恢复数据。

如果在AOF命令追加过程中发生宕机，由于延迟写的技术特点，AOF的RESP命令可能不完整（被截断）。遇到这种情况时，Redis会按照配置项`aof-load-truncated`
执行不同的处理策略。这个配置是告诉Redis启动时读取aof文件，如果发现文件被截断（不完整）时该如何处理：

- yes：则尽可能多的加载数据，并以日志的方式通知用户；
- no：则以系统错误的方式崩溃，并禁止启动，需要用户修复文件后再重启。

## 总结

Redis提供了两种持久化的选择：RDB支持以特定的实践间隔为数据集生成时间点快照；AOF把Redis
Server收到的每条写指令持久化到日志中，待Redis重启时通过重放命令恢复数据。日志格式为RESP协议，对日志文件只做append操作，无损坏风险。并且当AOF文件过大时可以自动重写压缩文件。

当然，如果你不需要对数据进行持久化，也可以禁用Redis的持久化功能，但是大多数情况并非如此。实际上，我们时有可能同时使用RDB和AOF两种方式的，最重要的就是我们要理解两者的区别，以便合理使用。

### RDB vs AOF

#### RDB优点

- RDB是一个紧凑压缩的二进制文件，代表Redis在某一个时间点上的数据快照，非常适合用于备份、全量复制等场景。
- RDB对灾难恢复、数据迁移非常友好，RDB文件可以转移至任何需要的地方并重新加载。
- RDB是Redis数据的内存快照，数据恢复速度较快，相比于AOF的命令重放有着更高的性能。

#### RDB缺点

-
RDB方式无法做到实时或秒级持久化。因为持久化过程是通过fork子进程后由子进程完成的，子进程的内存只是在fork操作那一时刻父进程的数据快照，而fork操作后父进程持续对外服务，内部数据时刻变更，子进程的数据不再更新，两者始终存在差异，所以无法做到实时性。
- RDB持久化过程中的fork操作，会导致内存占用加倍，而且父进程数据越多，fork过程越长。
- Redis请求高并发可能会频繁命中save规则，导致fork操作及持久化备份的频率不可控；
- RDB文件有文件格式要求，不同版本的Redis会对文件格式进行调整，存在老版本无法兼容新版本的问题。

#### AOF优点

- AOF持久化有更好的实时性，我们可以选择三种不同的方式（appendfsync）：no、every second、always，every second作为默认的策略具有最好的性能，极端情况下可能会丢失一秒的数据。
- AOF文件只有append操作，无复杂的seek等文件操作，没有损坏风险。即使最后写入数据被截断，也很容易使用`redis-check-aof`工具修复；
- 当AOF文件变大时，Redis可在后台自动重写。重写过程中旧文件会持续写入，重写完成后新文件将变得更小，并且重写过程中的增量命令也会append到新文件。
- AOF文件以已于理解与解析的方式包含了对Redis中数据的所有操作命令。即使不小心错误的清除了所有数据，只要没有对AOF文件重写，我们就可以通过移除最后一条命令找回所有数据。
- AOF已经支持混合持久化，文件大小可以有效控制，并提高了数据加载时的效率。

#### AOF缺点

- 对于相同的数据集合，AOF文件通常会比RDB文件大；
- 在特定的fsync策略下，AOF会比RDB略慢。一般来讲，fsync_every_second的性能仍然很高，fsync_no的性能与RDB相当。但是在巨大的写压力下，RDB更能提供最大的低延时保障。
- 在AOF上，Redis曾经遇到一些几乎不可能在RDB上遇到的罕见bug。一些特殊的指令（如BRPOPLPUSH）导致重新加载的数据与持久化之前不一致，Redis官方曾经在相同的条件下进行测试，但是无法复现问题。

### 使用建议

对RDB和AOF两种持久化方式的工作原理、执行流程及优缺点了解后，我们来思考下，实际场景中应该怎么权衡利弊，合理的使用两种持久化方式。如果仅仅是使用Redis作为缓存工具，所有数据可以根据持久化数据库进行重建，则可关闭持久化功能，做好预热、缓存穿透、击穿、雪崩之类的防护工作即可。

一般情况下，Redis会承担更多的工作，如分布式锁、排行榜、注册中心等，持久化功能在灾难恢复、数据迁移方面将发挥较大的作用。建议遵循几个原则：

- 不要把Redis作为数据库，所有数据尽可能可由应用服务自动重建。
- 使用4.0以上版本Redis，使用AOF+RDB混合持久化功能。
- 合理规划Redis最大占用内存，防止AOF重写或save过程中资源不足。
- 避免单机部署多实例。
- 生产环境多为集群化部署，可在slave开启持久化能力，让master更好的对外提供写服务。
- 备份文件应自动上传至异地机房或云存储，做好灾难备份。

### 关于fork()

通过上面的分析，我们都知道RDB的快照、AOF的重写都需要fork，这是一个重量级操作，会对Redis造成阻塞。因此为了不影响Redis主进程响应，我们需要尽可能降低阻塞。

- 降低fork的频率，比如可以手动来触发RDB生成快照、与AOF重写；
- 控制Redis最大使用内存，防止fork耗时过长；
- 使用更高性能的硬件；
- 合理配置Linux的内存分配策略，避免因为物理内存不足导致fork失败。

## redis备份操作

### 配置RDB

修改`redis.conf`的配置文件

![image-20220126151155980](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202201261511040.png)

![image-20220126151338325](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202201261513379.png)

从注释中可以看出来，这个地方的save并不是在控制台使用的`save`方法，因为这里配置的save是forl了一个子进程，所以对应的应该是`bgsave`

### 配置AOF

![image-20220126151420303](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202201261514351.png)

![image-20220126151438601](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202201261514646.png)

通过指定不同的配置方式，来启用不同方式的aof