HashMap 最早出现在 JDK 1.2 中，底层基于散列算法实现。HashMap 允许 null 键和 null 值，在计算哈键的哈希值时，null 键哈希值为 0。HashMap 并不保 证键值对的顺序，这意味着在进行某些操作后，键值对的顺序可能会发生变化。另外，需要注意的是，HashMap是非线程安全类，在多线程环境下可能会存在问题。

HashMap 最早在 JDK 1.2 中就出现了，底层是基于散列算法实现，随着几代的优 化更新到目前为止它的源码部分已经比较复杂，涉及的知识点也非常多，在 JDK 1.8 中包括：`1、散列表实现、2、扰动函数、3、初始化容量、4、负载因子、5、扩容元 素拆分、6、链表树化、7、红黑树、8、插入、9、查找、10、删除、11、遍历、12、分段锁`等等。

### 初步实现HashMap

#### 问题

假设我们有一组 7 个字符串，需要存放到数组中，但要求在获取每个元 素的时候时间复杂度是 O(1)。也就是说你不能通过循环遍历的方式进行获取， 而是要定位到数组 ID 直接获取相应的元素。

#### 方案

如果说我们需要通过 ID 从数组中获取元素，那么就需要把每个字符串都 计算出一个在数组中的位置 ID。字符串获取 ID 你能想到什么方式? 一个字符 串最直接的获取跟数字相关的信息就是 HashCode，可 HashCode 的取值范围太大了[-2147483648, 2147483647]，不可能直接使用。那么就需要使用 HashCode 与 数组长度做与运算，得到一个可以在数组中出现的位置。如果说有两个元素得到 同样的 ID，那么这个数组 ID 下就存放两个字符串。

#### 代码实现

```java
    @Test
    public void test_128hash() {

        // 初始化一组字符串
        List<String> list = new ArrayList<>();
        list.add("jlkk");
        list.add("lopi");
        list.add("小傅哥");
        list.add("e4we");
        list.add("alpo");
        list.add("yhjk");
        list.add("plop");

        // 定义要存放的数组
        String[] tab = new String[8];

        // 循环存放
        for (String key : list) {
            int idx = key.hashCode() & (tab.length - 1);  // 计算索引位置
            System.out.println(String.format("key值=%s Idx=%d", key, idx));
            if (null == tab[idx]) {
                tab[idx] = key;
                continue;
            }
            tab[idx] = tab[idx] + "->" + key;
        }
        // 输出测试结果
        System.out.println("测试结果：" + JSON.toJSONString(tab));
    }
```

#### 测试结果

![image-20211229210336721](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112292103765.png)

- 在测试结果首先是计算出每个元素在数组的 Idx，也有出现重复的位 置。
- 最后是测试结果的输出，1、3、6，位置是空的，2、5，位置有两个元素被链接起来 e4we->plop。
- 这就达到了我们一个最基本的要求，将串元素散列存放到数组中，最后通过字符串元素的索引 ID 进行获取对应字符串。这样是 HashMap 的一个 最基本原理，有了这个基础后面就会更容易理解 HashMap 的源码实现。

#### Hash散列图

![image-20211229210522517](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112292105554.png)

- 这张图就是上面代码实现的全过程，将每一个字符串元素通过 Hash 计算 索引位置，存放到数组中。
- 黄色的索引 ID 是没有元素存放、绿色的索引 ID 存放了一个元素、红色 的索引 ID 存放了两个元素。

上面实现的简单HashMap，或者说根本算不上HashMap，只能算作一个散列数据存放的雏形，但是这样一个数据结构放在实际使用中，会有哪些问题呢？

1. 这里所有的元素存放都需要获取一个索引位置，而如果元素的位置不够 散列碰撞严重，那么就失去了散列表存放的意义，没有达到预期的性能。
2. 在获取索引 ID 的计算公式中，需要数组长度是 2 的倍数，那么怎么进行 初始化这个数组大小。
3. 数组越小碰撞的越大，数组越大碰撞的越小，时间与空间如何取舍。
4. 目前存放 7 个元素，已经有两个位置都存放了 2 个字符串，那么链表越来越长怎么优化。
5. 随着元素的不断添加，数组长度不足扩容时，怎么把原有的元素，拆分到新的位置上去

### 扰动函数

```java
static final int hash(Object key) {
        int h;
        return (key == null) ? 0 : (h = key.hashCode()) ^ (h >>> 16);
    }
```

理论上来说字符串的 hashCode 是一个 int 类型值，那可以直接作为数组下标了， 且不会出现碰撞。但是这个hashCode的取值范围是[-2147483648, 2147483647]， 有将近 40 亿的长度，谁也不能把数组初始化的这么大，内存也是放不下的。

我们默认初始化的 Map 大小是 16 个长度 DEFAULT_INITIAL_CAPACITY = 1 << 4， 所以获取的 Hash 值并不能直接作为下标使用，需要与数组长度进行取模运算得 到一个下标值，也就是我们上面做的散列列子。

那么，hashMap 源码这里不只是直接获取哈希值，还进行了一次扰动计算，`(h = key.hashCode()) ^ (h >>> 16)`。把哈希值右移 16 位，也就正好是自己长度的一 半，之后与原哈希值做异或运算，这样就混合了原哈希值中的高位和低位，增大 了随机性。计算方式如下图;

![image-20211229211104405](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112292111461.png)

其实使用扰动函数就是为了增加随机性，让数据元素更加均衡的散列，减少碰撞。

#### 验证扰动函数

从上面的分析可以看出，扰动函数使用了哈希值的高半区和低半区做异或，混合 原始哈希码的高位和低位，以此来加大低位区的随机性。 

但看不到实验数据的话，这终究是一段理论，具体这段哈希值真的被增加了随机 性没有，并不知道。所以这里我们要做一个实验，这个实验是这样做;

1. 选取 10 万个单词词库
2. 定义 128 位长度的数组格子
3. 分别计算在扰动和不扰动下，10 万单词的下标分配到 128 个格子的数量
4. 统计各个格子数量，生成波动曲线。如果扰动函数下的波动曲线相对更平稳，那么证明扰动函数有效果。

```java
//扰动函数对比方法
public class Disturb {

    /**
     * 扰动函数 计算数组下标
     *
     * @param key
     * @param size
     * @return
     */
    public static int disturbHashIdx(String key, int size) {
        return (size - 1) & (key.hashCode() ^ (key.hashCode() >>> 16));
    }

    /**
     * 非扰动函数 计算数组下标
     *
     * @param key
     * @param size
     * @return
     */
    public static int hashIdx(String key, int size) {
        return (size - 1) & key.hashCode();
    }

}
```

```java
    @Before
    public void before() {
        // 读取文件，103976个英语单词库.txt
        words = FileUtil.readWordList("/Users/jiaxiansheng/develop/interview/interview-03/103976个英语单词库.txt");
    }

    @Test
    public void test_disturb() {
        Map<Integer, Integer> map = new HashMap<>(16);
        for (String word : words) {
            // 使用扰动函数
            int idx = Disturb.disturbHashIdx(word, 128);
            // 不使用扰动函数
            // int idx = Disturb.hashIdx(word, 128);
            if (map.containsKey(idx)) {
                Integer integer = map.get(idx);
                map.put(idx, ++integer);
            } else {
                map.put(idx, 1);
            }
        }
        System.out.println(map.values());
    }
```

以上分别统计两种函数下的下标值分配，最终将统计结果放到 excel 中生成图 表。

**未使用扰动函数**

![image-20211229212132542](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112292121576.png)

**使用扰动函数**

![image-20211229212104413](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112292121445.png)

- 从这两种的对比图可以看出来，在使用了扰动函数后，数据分配的更加 均匀了。
- 数据分配均匀，也就是散列的效果更好，减少了 hash 的碰撞，让数据存 放和获取的效率更佳。

### 初始化容量和负载因子

```java
/**
* The default initial capacity - MUST be a power of two.
*/
static final int DEFAULT_INITIAL_CAPACITY = 1 << 4;

/**
* The load factor used when none specified in constructor.
*/
static final float DEFAULT_LOAD_FACTOR = 0.75f;
```

如果在初始化HashMap的时候，如果传一个17个的值`new HashMap<>(17)`，那么Map会如何处理。

```java
    public HashMap(int initialCapacity, float loadFactor) {
        if (initialCapacity < 0)
            throw new IllegalArgumentException("Illegal initial capacity: " +
                                               initialCapacity);
        if (initialCapacity > MAXIMUM_CAPACITY)
            initialCapacity = MAXIMUM_CAPACITY;
        if (loadFactor <= 0 || Float.isNaN(loadFactor))
            throw new IllegalArgumentException("Illegal load factor: " +
                                               loadFactor);
        this.loadFactor = loadFactor;
        this.threshold = tableSizeFor(initialCapacity);
    }
```

- 阀值 threshold，通过方法 tableSizeFor 进行计算，是根据初始化来计算的。
- 这个方法也就是要寻找比初始值大的，最小的那个 2 进制数值。比如传 了 17，我应该找到的是 32。

#### 阈值

```java
    static final int tableSizeFor(int cap) {
        int n = cap - 1;
        n |= n >>> 1;
        n |= n >>> 2;
        n |= n >>> 4;
        n |= n >>> 8;
        n |= n >>> 16;
        return (n < 0) ? 1 : (n >= MAXIMUM_CAPACITY) ? MAXIMUM_CAPACITY : n + 1;
    }
```

- MAXIMUM_CAPACITY = 1 << 30，这个是临界范围，也就是最大的 Map 集 合。
- 乍一看可能有点晕怎么都在向右移位 1、2、4、8、16，这主要是为了 把二进制的各个位置都填上 1，当二进制的各个位置都是 1 以后，就是一个标准的 2 的倍数减 1 了，最后把结果加 1 再返回即可

那这里我们把 17 这样一个初始化计算阀值的过程，用图展示出来，方便理解;

![image-20211229212928632](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112292129677.png)

阈值有两个作用：

- 计算初始值，然后用做初始化map容量
- 作为扩容的判断标准，然后map容量大于阈值，那么map扩容

#### 负载因子

负载因子，可以理解成一辆车可承重重量超过某个阀值时，把货放到新的车上。

那么在 HashMap 中，负载因子决定了数据量多少了以后进行扩容。这里要到上 面做的 HashMap 例子，我们准备了 7 个元素，但是最后还有 3 个位置空余，2 个 位置存放了 2 个元素。 所以可能即使你数据比数组容量大时也是不一定能正正 好好的把数组占满的，而是在某些小标位置出现了大量的碰撞，只能在同一个位置用链表存放，那么这样就失去了 Map 数组的性能。

所以，要选择一个合理的大小下进行扩容，默认值 0.75 就是说当阀值容量占了 3/4 时赶紧扩容，减少 Hash 碰撞。

同时 0.75 是一个默认构造值，在创建 HashMap 也可以调整，比如你希望用更多 的空间换取时间，可以把负载因子调的更小一些，减少碰撞。

### 扩容

为什么扩容，因为数组长度不足了。那扩容最直接的问题，就是需要把元素拆分 到新的数组中。拆分元素的过程中，原 jdk1.7 中会需要重新计算哈希值，但是 到 jdk1.8 中已经进行优化，不在需要重新计算，提升了拆分的性能，设计的还 是非常巧妙的。

#### 测试

```java
@Test
public void test_hashMap() {
    List<String> list = new ArrayList<>();
    list.add("jlkk");
    list.add("lopi");
    list.add("jmdw");
    list.add("e4we");
    list.add("io98");
    list.add("nmhg");
    list.add("vfg6");
    list.add("gfrt");
    list.add("alpo");
    list.add("vfbh");
    list.add("bnhj");
    list.add("zuio");
    list.add("iu8e");
    list.add("yhjk");
    list.add("plop");
    list.add("dd0p");

    for (String key : list) {
        int hash = key.hashCode() ^ (key.hashCode() >>> 16);
        System.out.println("字符串：" + key + " \tIdx(16)：" + ((32 - 1) & hash) + " \tBit值：" + Integer.toBinaryString(hash) + " - " + Integer.toBinaryString(hash & 32) + " \t\tIdx(32)：" + ((64 - 1) & hash));
        System.out.println(Integer.toBinaryString(key.hashCode()) +" "+ Integer.toBinaryString(hash) + " " + Integer.toBinaryString((64 - 1) & hash));
    }
}
```

#### 测试结果

![image-20211229213606325](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112292136373.png)

- 这里我们随机使用一些字符串计算他们分别在 16 位长度和 32 位长度数 组下的索引分配情况，看哪些数据被重新路由到了新的地址。
- 同时，这里还可以观察出一个非常重要的信息，原哈希值与扩容新增出来的长度 16，进行&运算，如果值等于 0，则下标位置不变。如果不为 0，那么新的位置则是原来位置上加 16。{这个地方需要好好理解下， 并看实验数据}
- 这样一来，就不需要在重新计算每一个数组中元素的哈希值了。

### 数据迁移

![image-20211229213858779](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112292138820.png)

- 这张图就是原 16 位长度数组元素，向度中转移的过程。
- 其中黄色区域元素 zuio 因计算结果 hash & oldCap 不为 1，则被迁移到下标位置 24。
- 同时还是用重新计算哈希值的方式验证了，确实分配到 24 的位置，因为这是在二进制计算中补 1 的过程，所以可以通过上面简化的方式确定哈 希值的位置。

### 源码分析

通过上面的学习，相信对于HashMap也有了一定的了解，那么在分析源码的过程中先考虑下面的问题：

1. 如果出现哈希值计算的下标碰撞了怎么办?
2. 如果碰撞了是扩容数组还是把值存成链表结构，让一个节点有多个值存放呢? 
3. 如果存放的数据的链表过长，就失去了散列表的性能了，怎么办呢
4. 如果想解决链表过长，什么时候使用树结构呢，使用哪种树呢?

#### 插入

![image-20211229214415865](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112292144922.png)

以上就是 HashMap 中一个数据插入的整体流程，包括了;计算下标、何时扩容、 何时链表转红黑树等，具体如下：

1. 首先进行哈希值的扰动，获取一个新的哈希值。`(key == null) ? 0 : (h = key.hashCode()) ^ (h >>> 16)`;

2. 判断 tab 是否位空或者长度为 0，如果是则进行扩容操作。

   `**if** ((tab = table) == **null** || (n = tab.length) == 0) n = (tab = resize()).length`;

3. 根据哈希值计算下标，如果对应小标正好没有存放数据，则直接插入即可 否则需要覆盖。`tab[i = (n - 1) & hash])`

4. 判断 tab[i]是否为树节点，否则向链表中插入数据，是则向树中插入节 点。

5. 如果链表中插入节点的时候，链表长度大于等于 8，则需要把链表转换为 红黑树。`treeifyBin(tab, hash)`;

6. 最后所有元素处理完成后，判断是否超过阈值;`threshold`，超过则扩容。

7. 拆分散列的相应的桶节点上，也就把链表长度缩短了。

8. 最后所有元素处理完成后，判断是否超过阈值;threshold，超过则扩容。

9. `treeifyBin`,是一个链表转树的方法，但不是所有的链表长度为 8 后都会 转成树，还需要判断存放 key 值的数组桶长度是否小于 64 MIN_TREEIFY_CAPACITY。如果小于则需要扩容，扩容后链表上的数据会被拆分散列的相应的桶节点上，也就把链表长度缩短了。

```java
public V put(K key, V value) {
        return putVal(hash(key), key, value, false, true);
    }

    /**
     * Implements Map.put and related methods.
     *
     * @param hash hash for key
     * @param key the key
     * @param value the value to put
     * @param onlyIfAbsent if true, don't change existing value
     * @param evict if false, the table is in creation mode.
     * @return previous value, or null if none
     */
    final V putVal(int hash, K key, V value, boolean onlyIfAbsent,
                   boolean evict) {
        Node<K,V>[] tab; Node<K,V> p; int n, i;
        // 初始化桶数组 table，table 被延迟到插入新数据时再进行初始化
        if ((tab = table) == null || (n = tab.length) == 0)
            n = (tab = resize()).length;
        // 如果桶中不包含键值对节点引用，则将新键值对节点的引用存入桶中即可    
        if ((p = tab[i = (n - 1) & hash]) == null)
            tab[i] = newNode(hash, key, value, null);
        else {
            Node<K,V> e; K k;
            // 如果键的值以及节点 hash 等于链表中的第一个键值对节点时，则将 e 指向该键值对
            if (p.hash == hash &&
                ((k = p.key) == key || (key != null && key.equals(k))))
                e = p;
          // 如果桶中的引用类型为 TreeNode，则调用红黑树的插入方法
            else if (p instanceof TreeNode)
                e = ((TreeNode<K,V>)p).putTreeVal(this, tab, hash, key, value);
            else {
              // 对链表进行遍历，并统计链表长度
                for (int binCount = 0; ; ++binCount) {
                  // 链表中不包含要插入的键值对节点时，则将该节点接在链表的最后
                    if ((e = p.next) == null) {
                        p.next = newNode(hash, key, value, null);
                      // 如果链表长度大于或等于树化阈值，则进行树化操作
                        if (binCount >= TREEIFY_THRESHOLD - 1) // -1 for 1st
                            treeifyBin(tab, hash);
                        break;
                    }
                  // 条件为 true，表示当前链表包含要插入的键值对，终止遍历
                    if (e.hash == hash &&
                        ((k = e.key) == key || (key != null && key.equals(k))))
                        break;
                    p = e;
                }
            }
          // 判断要插入的键值对是否存在 HashMap 中
            if (e != null) { // existing mapping for key
                V oldValue = e.value;
              // onlyIfAbsent 表示是否仅在 oldValue 为 null 的情况下更新键值对的值
                if (!onlyIfAbsent || oldValue == null)
                    e.value = value;
                afterNodeAccess(e);
                return oldValue;
            }
        }
        ++modCount;
      // 键值对数量超过阈值时，则进行扩容
        if (++size > threshold)
            resize();
        afterNodeInsertion(evict);
        return null;
    }
```

#### 扩容

HashMap 是基于数组+链表和红黑树实现的，但用于存放 key 值得的数组桶的长 度是固定的，由初始化决定。 那么，随着数据的插入数量增加以及负载因子的作用下，就需要扩容来存放更多 的数据。而扩容中有一个非常重要的点，就是 jdk1.8 中的优化操作，可以不需要再重新计算每一个元素的哈希值.

在第一次插入数据的时候，会进行map的初始化，HashMap构造函数只是对一些信息进行了初始化，但是对于数组桶的初始化会放到第一次插入数据的时候操作；

![image-20211229213858779](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112292150275.png)

```java
final Node<K,V>[] resize() {
    Node<K,V>[] oldTab = table;
    int oldCap = (oldTab == null) ? 0 : oldTab.length;
    int oldThr = threshold;
    int newCap, newThr = 0;
  // Cap 是 capacity 的缩写，容量。如果容量不为空，则说明已经初始化。
    if (oldCap > 0) {
      // 如果容量达到最大 1 << 30 则不再扩容
        if (oldCap >= MAXIMUM_CAPACITY) {
            threshold = Integer.MAX_VALUE;
            return oldTab;
        }
      // 按旧容量和阀值的 2 倍计算新容量和阀值
        else if ((newCap = oldCap << 1) < MAXIMUM_CAPACITY &&
                 oldCap >= DEFAULT_INITIAL_CAPACITY)
            newThr = oldThr << 1; // double threshold
    }
    else if (oldThr > 0) // initial capacity was placed in threshold
      // initial capacity was placed in threshold 翻译过来的意思，如下; // 初始化时，将 threshold 的值赋值给 newCap，
// HashMap 使用 threshold 变量暂时保存 initialCapacity 参数的值
        newCap = oldThr;
    else {               // zero initial threshold signifies using defaults
      //调用无参构造方法时，数组桶数组容量为默认容量1 << 4；
      //阈值，是默认容量和负载因子的乘积，0.75
        newCap = DEFAULT_INITIAL_CAPACITY;
        newThr = (int)(DEFAULT_LOAD_FACTOR * DEFAULT_INITIAL_CAPACITY);
    }
  // newThr 为 0，则使用阀值公式计算容量
    if (newThr == 0) {
        float ft = (float)newCap * loadFactor;
        newThr = (newCap < MAXIMUM_CAPACITY && ft < (float)MAXIMUM_CAPACITY ?
                  (int)ft : Integer.MAX_VALUE);
    }
    threshold = newThr;
    @SuppressWarnings({"rawtypes","unchecked"})
  // 初始化数组桶，用于存放 key
    Node<K,V>[] newTab = (Node<K,V>[])new Node[newCap];
    table = newTab;
    if (oldTab != null) {
      // 如果旧数组桶，oldCap有值，则遍历将键值映射到新数组桶中
        for (int j = 0; j < oldCap; ++j) {
            Node<K,V> e;
            if ((e = oldTab[j]) != null) {
                oldTab[j] = null;
                if (e.next == null)
                    newTab[e.hash & (newCap - 1)] = e;
                else if (e instanceof TreeNode)
                  // 这里 split，是红黑树拆分操作。在重新映射时操作的。
                    ((TreeNode<K,V>)e).split(this, newTab, j, oldCap);
                else { // preserve order
                    Node<K,V> loHead = null, loTail = null;
                    Node<K,V> hiHead = null, hiTail = null;
                    Node<K,V> next;
                  // 这里是链表，如果当前是按照链表存放的，则将链表节点按原顺序进行分组
                    do {
                        next = e.next;
                        if ((e.hash & oldCap) == 0) {
                            if (loTail == null)
                                loHead = e;
                            else
                                loTail.next = e;
                            loTail = e;
                        }
                        else {
                            if (hiTail == null)
                                hiHead = e;
                            else
                                hiTail.next = e;
                            hiTail = e;
                        }
                    } while ((e = next) != null);
                  // 将分组后的链表映射到桶中
                    if (loTail != null) {
                        loTail.next = null;
                        newTab[j] = loHead;
                    }
                    if (hiTail != null) {
                        hiTail.next = null;
                        newTab[j + oldCap] = hiHead;
                    }
                }
            }
        }
    }
    return newTab;
}
```

以上的代码稍微有些长，但是整体的逻辑还是蛮清晰的，主要包括;

1. 扩容时计算出新的 newCap、newThr，这是两个单词的缩写，一个是 Capacity ， 另一个是阀 Threshold
2. newCap 用于创新的数组桶 new Node[newCap];
3. 随着扩容后，原来那些因为哈希碰撞，存放成链表和红黑树的元素，都需要进行拆 分存放到新的位置中。

#### 链表树化

HashMap 这种散列表的数据结构，最大的性能在于可以 O(1)时间复杂度定位到元 素，但因为哈希碰撞不得已在一个下标里存放多组数据，那么 jdk1.8 之前的设 计只是采用链表的方式进行存放，如果需要从链表中定位到数据时间复杂度就是 O(n)，链表越长性能越差。因为在 jdk1.8 中把过长的链表也就是 8 个，优化为 自平衡的红黑树结构，以此让定位元素的时间复杂度优化近似于 O(logn)，这样来提升元素查找的效率。但也不是完全抛弃链表，因为在元素相对不多的情况下， 链表的插入速度更快，所以综合考虑下设定阈值为 8 才进行红黑树转换操作。

![image-20211229215940163](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112292159211.png)

以上就是一组链表转换为红黑树的情况，元素包括;40、51、62、73、84、95、 150、161 这些是经过实际验证可分配到 Idx:12 的节点

```java
final void treeifyBin(Node<K,V>[] tab, int hash) {
    int n, index; Node<K,V> e;
  // 这块就是我们上面提到的，不一定树化还可能只是扩容。主要桶数组容量是否小于
64 MIN_TREEIFY_CAPACITY
    if (tab == null || (n = tab.length) < MIN_TREEIFY_CAPACITY)
        resize();
    else if ((e = tab[index = (n - 1) & hash]) != null) {
        TreeNode<K,V> hd = null, tl = null;
        do {
          // 将普通节点转换为树节点，但此时还不是红黑树，也就是说还不一定平衡
            TreeNode<K,V> p = replacementTreeNode(e, null);
            if (tl == null)
                hd = p;
            else {
                p.prev = tl;
                tl.next = p;
            }
            tl = p;
        } while ((e = e.next) != null);
        if ((tab[index] = hd) != null)
            hd.treeify(tab);
    }
}
```

以上源码主要包括的知识点如下;

1. 链表树化的条件有两点;**链表长度大于等于 8、桶容量大于 64**，否则只是扩容，不会树化。
2. 链表树化的过程中是先由链表转换为树节点，此时的树可能不是一颗平衡树。同时 在树转换过程中会记录链表的顺序，tl.next = p，这主要方便后续树转链表和 拆分更方便。
3. 链表转换成树完成后，在进行红黑树的转换。先简单介绍下，红黑树的转换需要染 色和旋转，以及比对大小。在比较元素的大小中，有一个比较有意思的方法， tieBreakOrder 加时赛，这主要是因为 HashMap 没有像 TreeMap 那样本身就 有 Comparator 的实现。

#### 红黑树转链表

```java
final Node<K,V> untreeify(HashMap<K,V> map) {
  Node<K,V> hd = null, tl = null;
  // 遍历 TreeNode
  for (Node<K,V> q = this; q != null; q = q.next) {
  // TreeNode 替换 Node
    Node<K,V> p = map.replacementNode(q, null);
    if (tl == null)
      hd = p;
    else
      tl.next = p;
    tl = p;
  }
  return hd;
}
```

红黑树转链表时候，直接把 TreeNode 转换为 Node 即可。

> 在调用删除方法的时候，如果一颗红黑树的长度小于等于6的时候，红黑树并不会转换成链表，红黑树转链表只有在调用resize方法的时候才会执行

#### 查找

![image-20211229220416297](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112292204368.png)

```java
public V get(Object key) {
    Node<K,V> e;
  // 同样需要经过扰动函数计算哈希值
    return (e = getNode(hash(key), key)) == null ? null : e.value;
}

/**
 * Implements Map.get and related methods.
 *
 * @param hash hash for key
 * @param key the key
 * @return the node, or null if none
 */
final Node<K,V> getNode(int hash, Object key) {
    Node<K,V>[] tab; Node<K,V> first, e; int n; K k;
  // 判断桶数组的是否为空和长度值
    if ((tab = table) != null && (n = tab.length) > 0 &&
        // 计算下标，哈希值与数组长度-1
        (first = tab[(n - 1) & hash]) != null) {
        if (first.hash == hash && // always check first node
            ((k = first.key) == key || (key != null && key.equals(k))))
            return first;
        if ((e = first.next) != null) {
          // TreeNode 节点直接调用红黑树的查找方法，时间复杂度 O(logn)
            if (first instanceof TreeNode)
                return ((TreeNode<K,V>)first).getTreeNode(hash, key);
          // 如果是链表就依次遍历查找
            do {
                if (e.hash == hash &&
                    ((k = e.key) == key || (key != null && key.equals(k))))
                    return e;
            } while ((e = e.next) != null);
        }
    }
    return null;
}
```

以上查找的代码还是比较简单的，主要包括以下知识点;

1. 扰动函数的使用，获取新的哈希值，这在上一章节已经讲过
2. 下标的计算，同样也介绍过 tab[(n - 1) & hash])
3. 确定了桶数组下标位置，接下来就是对红黑树和链表进行查找和遍历操作了

#### 删除

```java
public V remove(Object key) {
    Node<K,V> e;
    return (e = removeNode(hash(key), key, null, false, true)) == null ?
        null : e.value;
}
    final Node<K,V> removeNode(int hash, Object key, Object value,
                               boolean matchValue, boolean movable) {
        Node<K,V>[] tab; Node<K,V> p; int n, index;
      // 定位桶数组中的下标位置，index = (n - 1) & hash
        if ((tab = table) != null && (n = tab.length) > 0 &&
            (p = tab[index = (n - 1) & hash]) != null) {
            Node<K,V> node = null, e; K k; V v;
          // 如果键的值与链表第一个节点相等，则将 node 指向该节点
            if (p.hash == hash &&
                ((k = p.key) == key || (key != null && key.equals(k))))
                node = p;
            else if ((e = p.next) != null) {
              // 树节点，调用红黑树的查找方法，定位节点。
                if (p instanceof TreeNode)
                    node = ((TreeNode<K,V>)p).getTreeNode(hash, key);
                else {
                  // 遍历链表，找到待删除节点
                    do {
                        if (e.hash == hash &&
                            ((k = e.key) == key ||
                             (key != null && key.equals(k)))) {
                            node = e;
                            break;
                        }
                        p = e;
                    } while ((e = e.next) != null);
                }
            }
          // 删除节点，以及红黑树需要修复，因为删除后会破坏平衡性。链表的删除更加简单。
            if (node != null && (!matchValue || (v = node.value) == value ||
                                 (value != null && value.equals(v)))) {
                if (node instanceof TreeNode)
                    ((TreeNode<K,V>)node).removeTreeNode(this, tab, movable);
                else if (node == p)
                    tab[index] = node.next;
                else
                    p.next = node.next;
                ++modCount;
                --size;
                afterNodeRemoval(node);
                return node;
            }
        }
        return null;
    }
```

- 删除的操作也比较简单，这里面都没有太多的复杂的逻辑。 
- 另外红黑树的操作因为被包装了，只看使用上也是很容易。