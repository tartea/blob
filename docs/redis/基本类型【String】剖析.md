### String字符串

------

#### 基本操作

```shell
//设置值
set key 'value'
//添加过期时间
SET key value [EX seconds] [PX milliseconds] [NX|XX]
//获取值
get key
//判断是否存在
EXISTS key

//当键不存在的时候才可以添加
//基于此可实现分布式锁。 用 del key 释放锁。
SETNX key '1234'

//整数
set number 10
//加1
incr number
//加指定数据
incrby number 100
//减1
decr number

//一次对多个键赋值
MSET key1 value1 key2 value2
//同时获取多个键的值
mget key1 key2

//追加内容
APPEND key1 key
```

#### 存储原理

**数据模型**

**set name javaHuang** 为例，因为 Redis 是 KV 的数据库，它是通过 hashtable 实现的（我们把这个叫做外层的哈希）。所以每个键值对都会有一个 dictEntry，里面指向了 key 和 value
的指针。next 指向下一个 dictEntry。源码如下：

```
typedef struct dictEntry {
void *key; /* key 关键字定义 */
union {
void *val; uint64_t u64; /* value 定义 */
int64_t s64; double d;
} v;
struct dictEntry *next; /* 指向下一个键值对节点 */
} dictEntry；
```

<img src="https://gitee.com/gluten/images/raw/master/images/202111231714165.png" alt="image-20211123171432011" style="zoom:40%;" />

key 是字符串，但是 Redis 没有直接使用 C 的字符数组，而是存储在自定义的 SDS中。

value 既不是直接作为字符串存储，也不是直接存储在 SDS 中，而是存储在redisObject 中。实际上五种常用的数据类型的任何一种，都是通过 redisObject 来存储的。

**redisObject**

redisObject 的定义的源码如下：

```
typedef struct redisObject {
unsigned type:4; /* 对象的类型， 包括： OBJ_STRING、 OBJ_LIST、 OBJ_HASH、 OBJ_SET、 OBJ_ZSET */
unsigned encoding:4; /* 具体的数据结构 */
unsigned lru:LRU_BITS; /* 24 位， 对象最后一次被命令程序访问的时间， 与内存回收有关 */
int refcount; /* 引用计数。 当 refcount 为 0 的时候， 表示该对象已经不被任何对象引用， 则可以进行垃圾回收了
*/
void *ptr; /* 指向对象实际的数据结构 */
} robj
```

**可以使用 type 命令来查看对外的类型。**

```
127.0.0.1:6379> set name zhangsan
OK
127.0.0.1:6379> get name
"zhangsan"
127.0.0.1:6379> type name
string
```

**下面我来设置三种Key**

```
127.0.0.1:6379> set intNumber 1
OK
127.0.0.1:6379> set embstrStr 'aaaaaaaaaaaaaaaaaaaaaaaaa'
OK
127.0.0.1:6379> set rawStr 'ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss'
OK
```

**然后我们获取这三种Key的内部编码**

```
127.0.0.1:6379> object encoding intNumber
"int"
127.0.0.1:6379> object encoding embstrStr
"embstr"
127.0.0.1:6379> object encoding rawStr
"raw"
```

**于是我们可知，字符串类型的内部编码有三种：**

1. int，存储 8 个字节的长整型（long，2^63-1）
2. embstr, 代表 embstr 格式的 SDS（Simple Dynamic String 简单动态字符串,存储小于 44 个字节的字符串。
3. raw，存储大于 44 个字节的字符串（3.2 版本之前是 39 字节）。

### SDS

SDS是Redis 中字符串的实现。

在 3.2 以后的版本中，SDS 又有多种结构（sds.h）：sdshdr5、sdshdr8、sdshdr16、sdshdr32、sdshdr64，用于存储不同的长度的字符串，分别代表
2^5=32byte，2^8=256byte，2^16=65536byte=64KB，2^32byte=4GB。

```
struct __attribute__ ((__packed__)) sdshdr8 {
  uint8_t len; /* 当前字符数组的长度 */
  uint8_t alloc; /*当前字符数组总共分配的内存大小 */
  unsigned char flags; /* 当前字符数组的属性、 用来标识到底是 sdshdr8 还是 sdshdr16 等 */
  char buf[]; /* 字符串真正的值 */
};
```

<img src="https://gitee.com/gluten/images/raw/master/images/202111231720844.png" alt="image-20211123172052808" style="zoom:50%;" />

#### **为什么 Redis 要用 SDS 实现字符串？**

我们知道，C 语言本身没有字符串类型（只能用字符数组 char[]实现）。

1、使用字符数组必须先给目标变量分配足够的空间，否则可能会溢出。

2、如果要获取字符长度，必须遍历字符数组，时间复杂度是 O(n)。

3、C 字符串长度的变更会对字符数组做内存重分配。

4、通过从字符串开始到结尾碰到的第一个'\0'来标记字符串的结束，因此不能保存图片、音频、视频、压缩文件等二进制(bytes)保存的内容，二进制不安全。

*SDS 的特点：*

1、不用担心内存溢出问题，如果需要会对 SDS 进行扩容。

2、获取字符串长度时间复杂度为 O(1)，因为定义了 len 属性。

3、通过“空间预分配”（ sdsMakeRoomFor）和“惰性空间释放”，防止多次重分配内存。

4、判断是否结束的标志是 len 属性（它同样以'\0'结尾是因为这样就可以使用 C 语言中函数库操作字符串的函数了），可以包含'\0'。

#### **embstr 和 raw 的区别**

embstr 的使用只分配一次内存空间（因为 RedisObject 和 SDS 是连续的），而 raw需要分配两次内存空间（分别为 RedisObject 和 SDS 分配空间）。

因此与 raw 相比，embstr 的好处在于创建时少分配一次空间，删除时少释放一次空间，以及对象的所有数据连在一起，寻找方便。

而 embstr 的坏处也很明显，如果字符串的长度增加需要重新分配内存时，整个RedisObject 和 SDS 都需要重新分配空间，因此 Redis 中的 embstr 实现为只读。

#### **int 和 embstr 什么时候转化为 raw**

当 int 数 据 不 再 是 整 数 ， 或 大 小 超 过 了 long 的 范 围（2^63-1=9223372036854775807）时，自动转化为 embstr。

```
127.0.0.1:6379> append intNumber a
(integer) 2
127.0.0.1:6379> object encoding intNumber
"raw"
```

#### **明明没有超过阈值，为什么变成 raw 了**

```
127.0.0.1:6379> object encoding embstrStr
"embstr"
127.0.0.1:6379> append embstrStr test
(integer) 29
127.0.0.1:6379> object encoding embstrStr
"raw"
```

对于 embstr，由于其实现是只读的，因此在对 embstr 对象进行修改时，都会先转化为 raw 再进行修改。

因此，只要是修改 embstr 对象，修改后的对象一定是 raw 的，无论是否达到了 44个字节。

#### **当长度小于阈值时，会还原吗**

关于 Redis 内部编码的转换，都符合以下规律：编码转换在 Redis 写入数据时完成，且转换过程不可逆，只能从小内存编码向大内存编码转换（但是不包括重新 set）。

#### **为什么要对底层的数据结构进行一层包装呢**

通过封装，可以根据对象的类型动态地选择存储结构和可以使用的命令，实现节省空间和优化查询速度。
