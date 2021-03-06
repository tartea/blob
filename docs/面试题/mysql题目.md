#### redo log的概念是什么？为什么会存在。

redo log在mysql中属于InnoDB特有的日志系统，用于做操作日志存储使用的

由于mysql自带的引擎是MyISAM,它的日志为binlog，所以并没有`crash-safe`功能，所以InnoDB就自己实现了一套日志系统，用于保证`crash-safe`功能

#### 什么是WAL（write ahead log）机制，好处是什么。

预先写日志，将操作日志写入到redo log中，如果某一天数据库崩溃了，那么我们可以通过undo log来回滚日志。

#### binlog的概念是什么，起到什么作用，可以做crash safe吗。

bin log是用作日志归档使用的，因为它的机制是追加写，所以可以有无限的空间，我们会使用它作为数据恢复和主从复制的主要因素，另外它不可以作crash safe。

#### bin log和redo log的不同点有哪些

- redo log是InnoDB独有的，但是bin log是Mysql所有的东西，是所有引擎共同拥有的
- redo log 记录的是物理日志，指的是在在某个数据页上做了什么操作，bin log是在逻辑日志，记录的是sql语句的内容，如果在ID = 2这一行上加1.
- redo log的空间是有限的，如果日志记录的过程中空间满的话，会将内容刷取到磁盘上，但是bin log是可以追加记录到，可以无限记录

#### 执行器和innoDB在执行update语句时候的流程是什么样的

1. 获取指定行的数据
2. 如果内存中不存在该条数据，那么会从数据库中查到指定的数据
3. 将这一行数据更新，然后写入新行
4. 新行更新到内存中
5. 写入redo log日志，处于prepare阶段
6. 写入bin log日志
7. 提交事务，处于commit阶段

#### 如果数据库误操作，如何执行数据恢复

首先判断是否开启了bin log，然后找到之前备份的数据，再根据删除之前的binlog去恢复数据。

#### 什么是两阶段提交，为什么需要两阶段提交，两阶段提交怎么保证数据库中两份日志间的逻辑一致性（什么叫逻辑一致性）

就是在提交事务的时候先对redo log做一个prepare的操作，然后等bin log也写入成功后，在对redo log做commit操作。

两阶段提交主要是为了保证数据的一致性

如果在redo log记录阶段，mysql出现了crash，那么再次启动的时候，会发现只有redo log中存在一个XID（prepare阶段redo会在全局记录一个XID，后面的bin
log也是记录一个同样的XID），那么事务会回滚，如果两个log上都存在了XID，那么事务会commit

#### 如果不是两阶段提交，先写redo log和先写bin log两种情况各会遇到什么问题

1. **先写 redo log 后写 binlog**。假设在 redo log 写完，binlog 还没有写完的时候，MySQL 进程异常重启。由于我们前面说过的，redo log
   写完之后，系统即使崩溃，仍然能够把数据恢复回来，所以恢复后这一行 c 的值是 1。但是由于 binlog 没写完就 crash 了，这时候 binlog 里面就没有记录这个语句。因此，之后备份日志的时候，存起来的 binlog
   里面就没有这条语句。然后你会发现，如果需要用这个 binlog 来恢复临时库的话，由于这个语句的 binlog 丢失，这个临时库就会少了这一次更新，恢复出来的这一行 c 的值就是 0，与原库的值不同。
2. **先写 binlog 后写 redo log**。如果在 binlog 写完之后 crash，由于 redo log 还没写，崩溃恢复以后这个事务无效，所以这一行 c 的值是 0。但是 binlog 里面已经记录了“把 c 从 0
   改成 1”这个日志。所以，在之后用 binlog 来恢复的时候就多了一个事务出来，恢复出来的这一行 c 的值就是 1，与原库的值不同。

![mysql执行流程图](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202201170955454.png)

### 三大范式？

- 确保每列的原子性
- 确保每列都和主键相关
- 确保每列都和主键是直接相关，不是间接相关

### Innodb与MyIsam的区别？

innodb支持事务，但是myIsam不支持，Innodb支持外键，myIsam不支持，Innodb是聚集索引，myIsam不是，聚集索引所有的数据都在叶子结点上，所以在查询数据的时候有回表的操作，Innodb支持行级锁

### 为什么自增主键不连续

如果在插入数据的时候，出现了异常，如键冲突，那么下次在插入数据的时候，就会出现自增主键不连续了

### Innodb为什么推荐用自增ID

因为Innodb使用的是聚集索引，所以数据都是在叶子结点上的，而它们是以内存页的方式分布的，内存页上的数据是根据主键有序分布的，如果使用自增主键，那么数据会变得很紧凑
