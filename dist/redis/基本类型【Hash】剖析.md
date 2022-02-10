**redis的hash格式**

![image-20220126101535641](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202201261015686.png)

### **存储类型**

------

包含键值对的无序散列表。value 只能是字符串，不能嵌套其他类型。 

同样是存储字符串，Hash 与 String 的主要区别？

1. 把所有相关的值聚集到一个 key 中，节省内存空间 
2. 只使用一个 key，减少 key 冲突 
3. 当需要批量获取值的时候，只需要使用一个命令，减少内存/IO/CPU 的消耗

Hash 不适合的场景： 

1. Field 不能单独设置过期时间 
2. 没有 bit 操作 
3. 需要考虑数据量分布的问题（value 值非常大的时候，无法分布到多个节点）

### 操作命令

------

[操作手册](http://redisdoc.com/hash/hincrby.html)

```
127.0.0.1:6379[1]> hset web session sessionValue
(integer) 1
127.0.0.1:6379[1]> hget web session
"sessionValue"
127.0.0.1:6379[1]> HEXISTS web session
(integer) 1
127.0.0.1:6379[1]> HSETNX web cookie cookieValue
(integer) 1
```

### 存储（实现）原理

Redis 的 Hash 本身也是一个 KV 的结构，类似于 Java 中的 HashMap。 

外层的哈希（Redis KV 的实现）只用到了 hashtable。当存储 hash 数据类型时， 

我们把它叫做内层的哈希。内层的哈希底层可以使用两种数据结构实现： 

ziplist：OBJ_ENCODING_ZIPLIST（压缩列表） 

hashtable：OBJ_ENCODING_HT（哈希表）ob

```
127.0.0.1:6379[1]> OBJECT encoding web
"ziplist"
```

**那么在什么时候会用到ziplist，什么时候用到hashtable呢？**

```
# Hashes are encoded using a memory efficient data structure when they have a
# small number of entries, and the biggest entry does not exceed a given
# threshold. These thresholds can be configured using the following directives.
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
```

**源码**（新版中已经在使用listpack去取代ziplist）

```
/* 源码位置： t_hash.c ， 当达字段个数超过阈值， 使用 HT 作为编码 */
if (hashTypeLength(o) > server.hash_max_ziplist_entries)
hashTypeConvert(o, OBJ_ENCODING_HT);
/*源码位置： t_hash.c， 当字段值长度过大， 转为 HT */
for (i = start; i <= end; i++) {
if (sdsEncodedObject(argv[i]) &&
sdslen(argv[i]->ptr) > server.hash_max_ziplist_value)
{
hashTypeConvert(o, OBJ_ENCODING_HT);
break;
}
}
```

从而我们可以得知，当 hash 对象同时满足以下两个条件的时候，使用 ziplist 编码：

1. 所有的键值对的健和值的字符串长度都小于等于 **64byte**（一个英文字母一个字节）；
2. 哈希对象保存的键值对数量小于 **512** 个。一个哈希对象超过配置的阈值（键和值的长度有**>64byte**，键值对个数**>512** 个）时，会转换成哈希表（hashtable）。

**什么是ziplist压缩列表？**

​			ziplist 是一个经过特殊编码的双向链表，它不存储指向上一个链表节点和指向下一 

个链表节点的指针，而是存储上一个节点长度和当前节点长度，通过牺牲部分读写性能， 

来换取高效的内存空间利用率，是一种时间换空间的思想。只用在字段个数少，字段值 

小的场景里面。

**总体架构**

<img src="https://gitee.com/gluten/images/raw/master/images/202111250955258.png" alt="image-20211125095553216" style="zoom:50%;" />

```
typedef struct zlentry { 
unsigned int prevrawlensize; /* 上一个链表节点占用的长度 */ 
unsigned int prevrawlen; /* 存储上一个链表节点的长度数值所需要的字节数 */ 
unsigned int lensize; /* 存储当前链表节点长度数值所需要的字节数 */ 
unsigned int len; /* 当前链表节点占用的长度 */ 
unsigned int headersize; /* 当前链表节点的头部大小（prevrawlensize + lensize），即非数据域的大小 */ 
unsigned char encoding; /* 编码方式 */ 
unsigned char *p; /* 压缩链表以字符串的形式保存，该指针指向当前节点起始位置 */ 
} zlentry;
```

**什么是hashtable（ dict）？**

在 Redis 中，hashtable 被称为字典（dictionary），它是一个数组+链表的结构。前面我们知道了，Redis 的 KV 结构是通过一个 dictEntry 来实现的。Redis 又对 dictEntry 进行了多层的封装。

dictEntry 定义如下：

```
typedef struct dictEntry {
  void *key; /* key 关键字定义 */
  union {
    void *val; uint64_t u64; /* value 定义 */
    int64_t s64; double d;
  } v;
  struct dictEntry *next; /* 指向下一个键值对节点 */
} dictEntry
```

dictEntry 放到了 dictht（hashtable 里面）：

```
/* This is our hash table structure. Every dictionary has two of this as we
* implement incremental rehashing, for the old to the new table. */
typedef struct dictht {
  dictEntry **table; /* 哈希表数组 */
  unsigned long size; /* 哈希表大小 */
  unsigned long sizemask; /* 掩码大小， 用于计算索引值。 总是等于 size-1 */
  unsigned long used; /* 已有节点数 */
} dictht;
```

dictht 放到了 dict 里面：

```
typedef struct dict {
  dictType *type; /* 字典类型 */
  void *privdata; /* 私有数据 */
  dictht ht[2]; /* 一个字典有两个哈希表 */
  long rehashidx; /* rehash 索引 */
  unsigned long iterators; /* 当前正在使用的迭代器数量 */
} dict;
```

**从最底层到最高层 dictEntry——dictht——dict——OBJ_ENCODING_HT**

**哈希的总体存储结构如下：**

<img src="https://gitee.com/gluten/images/raw/master/images/202111250958443.png" alt="image-20211125095806409" style="zoom:50%;" />

注意： dictht 后面是 NULL 说明第二个 ht 还没用到。 dictEntry*后面是 NULL 说明没有 hash 到这个地址。 dictEntry 后面是NULL 说明没有发生哈希冲突。

**从`dict`中可以看到一个字典有两个hash表，为什么要定义两个hash表呢？ht[2]?**

redis 的 hash 默认使用的是 ht[0]，ht[1]不会初始化和分配空间。

哈希表 dictht 是用链地址法来解决碰撞问题的。在这种情况下，哈希表的性能取决于它的大小（size 属性）和它所保存的节点的数量（used 属性）之间的比率：

1.  比率在 1:1 时（一个哈希表 ht 只存储一个节点 entry），哈希表的性能最好；
2. 如果节点数量比哈希表的大小要大很多的话（这个比例用 ratio 表示，5 表示平均一个 ht 存储 5 个 entry），那么哈希表就会退化成多个链表，哈希表本身的性能优势就不再存在。

**在这种情况下需要扩容。Redis 里面的这种操作叫做 rehash。**

1. 为字符 ht[1]哈希表分配空间，这个哈希表的空间大小取决于要执行的操作，以及 ht[0]当前包含的键值对的数量。

   扩展：ht[1]的大小为第一个大于等于 ht[0].used*2。

2. 将所有的 ht[0]上的节点 rehash 到 ht[1]上，重新计算 hash 值和索引，然后放入指定的位置。

3. 当 ht[0]全部迁移到了 ht[1]之后，释放 ht[0]的空间，将 ht[1]设置为 ht[0]表，并创建新的 ht[1]，为下次 rehash 做准备。

**什么时候触发扩容？**

关键因素：负载因子

```
/* Using dictEnableResize() / dictDisableResize() we make possible to
 * enable/disable resizing of the hash table as needed. This is very important
 * for Redis, as we use copy-on-write and don't want to move too much memory
 * around when there is a child performing saving operations.
 *
 * Note that even when dict_can_resize is set to 0, not all resizes are
 * prevented: a hash table is still allowed to grow if the ratio between
 * the number of elements and the buckets > dict_force_resize_ratio. */
static int dict_can_resize = 1;
static unsigned int dict_force_resize_ratio = 5;
```

ratio = used / size，已使用节点与字典大小的比例。

dict_can_resize 为 1 并且 dict_force_resize_ratio 已使用节点数和字典大小之间的比率超过 1：5，触发扩容。

扩容判断 _dictExpandIfNeeded源码如下：

```
/* Expand the hash table if needed */
static int _dictExpandIfNeeded(dict *d)
{
    /* Incremental rehashing already in progress. Return. */
    if (dictIsRehashing(d)) return DICT_OK;

    /* If the hash table is empty expand it to the initial size. */
    if (DICTHT_SIZE(d->ht_size_exp[0]) == 0) return dictExpand(d, DICT_HT_INITIAL_SIZE);

    /* If we reached the 1:1 ratio, and we are allowed to resize the hash
     * table (global setting) or we should avoid it but the ratio between
     * elements/buckets is over the "safe" threshold, we resize doubling
     * the number of buckets. */
    if (d->ht_used[0] >= DICTHT_SIZE(d->ht_size_exp[0]) &&
        (dict_can_resize ||
         d->ht_used[0]/ DICTHT_SIZE(d->ht_size_exp[0]) > dict_force_resize_ratio) &&
        dictTypeExpandAllowed(d))
    {
        return dictExpand(d, d->ht_used[0] + 1);
    }
    return DICT_OK;
}
```

扩展源码

```
/* Expand or create the hash table,
 * when malloc_failed is non-NULL, it'll avoid panic if malloc fails (in which case it'll be set to 1).
 * Returns DICT_OK if expand was performed, and DICT_ERR if skipped. */
int _dictExpand(dict *d, unsigned long size, int* malloc_failed)
{
    if (malloc_failed) *malloc_failed = 0;

    /* the size is invalid if it is smaller than the number of
     * elements already inside the hash table */
    if (dictIsRehashing(d) || d->ht_used[0] > size)
        return DICT_ERR;

    /* the new hash table */
    dictEntry **new_ht_table;
    unsigned long new_ht_used;
    signed char new_ht_size_exp = _dictNextExp(size);

    /* Detect overflows */
    size_t newsize = 1ul<<new_ht_size_exp;
    if (newsize < size || newsize * sizeof(dictEntry*) < newsize)
        return DICT_ERR;

    /* Rehashing to the same table size is not useful. */
    if (new_ht_size_exp == d->ht_size_exp[0]) return DICT_ERR;

    /* Allocate the new hash table and initialize all pointers to NULL */
    if (malloc_failed) {
        new_ht_table = ztrycalloc(newsize*sizeof(dictEntry*));
        *malloc_failed = new_ht_table == NULL;
        if (*malloc_failed)
            return DICT_ERR;
    } else
        new_ht_table = zcalloc(newsize*sizeof(dictEntry*));

    new_ht_used = 0;

    /* Is this the first initialization? If so it's not really a rehashing
     * we just set the first hash table so that it can accept keys. */
    if (d->ht_table[0] == NULL) {
        d->ht_size_exp[0] = new_ht_size_exp;
        d->ht_used[0] = new_ht_used;
        d->ht_table[0] = new_ht_table;
        return DICT_OK;
    }

    /* Prepare a second hash table for incremental rehashing */
    d->ht_size_exp[1] = new_ht_size_exp;
    d->ht_used[1] = new_ht_used;
    d->ht_table[1] = new_ht_table;
    d->rehashidx = 0;
    return DICT_OK;
}
```

缩小容量

```

/* Resize the table to the minimal size that contains all the elements,
 * but with the invariant of a USED/BUCKETS ratio near to <= 1 */
int dictResize(dict *d)
{
    unsigned long minimal;

    if (!dict_can_resize || dictIsRehashing(d)) return DICT_ERR;
    minimal = d->ht_used[0];
    if (minimal < DICT_HT_INITIAL_SIZE)
        minimal = DICT_HT_INITIAL_SIZE;
    return dictExpand(d, minimal);
}
```

### **应用场景**

**String**

String 可以做的事情，Hash 都可以做。

**存储对象类型的数据**

比如对象或者一张表的数据，比 String 节省了更多 key 的空间，也更加便于集中管理。

**购物车**

<img src="https://gitee.com/gluten/images/raw/master/images/202111251016915.png" alt="image-20211125101632880" style="zoom:50%;" />

<img src="https://gitee.com/gluten/images/raw/master/images/202111251039969.png" alt="image-20211125103928933" style="zoom:50%;" />

key：用户 id；

field：商品 id；

value：商品数量。

+1：hincr。

-1：hdecr。

删除：hdel。

全选：hgetall。

商品数：hlen。

### 参考资料

原创作者：https://zhuanlan.zhihu.com/p/87968907
