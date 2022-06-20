ArrayList 的数据结构是基于数组实现的，只不过这个数组不像我们普通定义的 数组，它可以在 ArrayList 的管理下插入数据时按需动态扩容、数据拷贝等操作。

### 初始化

```java
    public ArrayList() {
        this.elementData = DEFAULTCAPACITY_EMPTY_ELEMENTDATA;
    }
    public ArrayList(int initialCapacity) {
        if (initialCapacity > 0) {
            this.elementData = new Object[initialCapacity];
        } else if (initialCapacity == 0) {
            this.elementData = EMPTY_ELEMENTDATA;
        } else {
            throw new IllegalArgumentException("Illegal Capacity: "+
                                               initialCapacity);
        }
    }
    public ArrayList(Collection<? extends E> c) {
        elementData = c.toArray();
        if ((size = elementData.length) != 0) {
            // c.toArray might (incorrectly) not return Object[] (see 6260652)
            if (elementData.getClass() != Object[].class)
                elementData = Arrays.copyOf(elementData, size, Object[].class);
        } else {
            // replace with empty array.
            this.elementData = EMPTY_ELEMENTDATA;
        }
    }
```

- 通常情况空构造函数初始化 ArrayList 更常用，这种方式数组的长度会在第一次插 入数据时候进行设置。
- 当我们已经知道要填充多少个元素到 ArrayList 中，比如 500 个、1000 个，那么为 了提供性能，减少 ArrayList 中的拷贝操作，这个时候会直接初始化一个预先设定 好的长度。
- 另外，`EMPTY_ELEMENTDATA` 是一个定义好的空对象;`private static final Object[] EMPTY_ELEMENTDATA = {}`

#### 构造

```java
 @Test
    public void init_01() {
        ArrayList<String> list = new ArrayList<String>();
        list.add("aaa");
        list.add("bbb");
        list.add("ccc");
    }

    @Test
    public void init_02() {

        List<String> list = Arrays.asList("aaa", "bbb", "ccc");
        list.add("ddd");

        ArrayList<String> obj = new ArrayList<String>(Arrays.asList("aaa", "bbb", "ccc"));

    }

    @Test
    public void init_03() {
        ArrayList<String> list = new ArrayList<String>() {{
            add("aaa");
            add("bbb");
            add("ccc");
        }};
    }
```

- 通过构造函数可以看到，只要实现 Collection 类的都可以作为入参。
- 在通过转为数组以及拷贝 Arrays.copyOf 到 Object[]集合中在赋值给属性elementData。

> c.toArray存在一个bug，具体可以看 [https://bugs.java.com/bugdatabase/view_bug.do?bug_id=6260652](https://bugs.java.com/bugdatabase/view_bug.do?bug_id=6260652)
>
> ```java
>     @Test
>     public void t() {
>         List<Integer> list1 = Arrays.asList(1, 2, 3);
>         System.out.println("通过数组转换：" + (list1.toArray().getClass() == Object[].class));
> 
>         ArrayList<Integer> list2 = new ArrayList<Integer>(Arrays.asList(1, 2, 3));
>         System.out.println("通过集合转换：" + (list2.toArray().getClass() == Object[].class));
>     }
> ```
>
> 测试结果
>
> 通过数组转换：false
> 通过集合转换：true
>
> - public Object[] toArray() 返回的类型不一定就是 Object[]，其类型 取决于其返回的实际类型，毕竟 Object 是父类，它可以是其他任意类型。
> - 子类实现和父类同名的方法，仅仅返回值不一致时，默认调用的是子类的实现方 法。
>
> 造成这个结果的原因，如下：
>
> 1. Arrays.asList 使用的是:Arrays.copyOf(this.a, size,(Class<? extends T[]>) a.getClass());
> 2. ArrayList 构造函数使用的是:Arrays.copyOf(elementData, size, Object[].class);

#### Arrays.asList

![image-20211229224702371](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112292247426.png)

从以上的类图关系可以看到：

1. 这两个 List 压根不同一个东西，而且 Arrasys 下的 List 是一个私有类，只能通过 asList 使用，不能单独创建。
2. 另外还有这个 ArrayList 不能添加和删除，主要是因为它的实现方式，可以参考 Arrays
   类中，这部分源码;`private static class ArrayList<E> extends AbstractList<E> implements RandomAccess, java.io.Serializable`

![image-20211229224938528](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112292249560.png)

可以看到`AbstractList`方法中的add和remove方法都是直接抛出异常，所以`Arrays.asList`生成的list是无法添加和删除的。

此外，Arrays 是一个工具包，里面还有一些非常好用的方法，例如;二分查找 *Arrays.binarySearch*、排序 *Arrays.sort* 等

### 插入

```java
public boolean add(E e) {
        ensureCapacityInternal(size + 1);  // Increments modCount!!
        elementData[size++] = e;
        return true;
    }
```

#### 扩容

在前面初始化部分讲到，ArrayList 默认初始化时会申请 10 个长度的空间，如果 超过这个长度则需要进行扩容，那么它是怎么扩容的呢?

从根本上分析来说，数组是定长的，如果超过原来定长长度，扩容则需要申请新 的数组长度，并把原数组元素拷贝到新数组中，如下图;

![image-20211229225642036](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112292256095.png)

图中介绍了当 List 结合可用空间长度不足时则需要扩容，这主要包括如下步骤;

1. 判断长度充足;ensureCapacityInternal(size + 1);
2. 当判断长度不足时，则通过扩大函数，进行扩容;grow(int minCapacity)
3. 扩容的长度计算;int newCapacity = oldCapacity + (oldCapacity >> 1);，旧容量 + 旧容量右移 1 位，这相当于扩容了原来容量的(int)3/2。原来是10，扩容时:1010 +
   1010 >> 1 = 1010 + 0101 = 10 + 5 = 15 ；原来是7，扩容时:0111 + 0111 >> 1 = 0111 + 0011 = 7 + 3 = 10
4. 当扩容完以后，就需要进行把数组中的数据拷贝到新数组中，这个过程会用到 Arrays.copyOf(elementData, newCapacity);，但他的底层用到的 是;System.arraycopy

#### 扩容函数

```java
private void grow(int minCapacity) {
    // overflow-conscious code
    int oldCapacity = elementData.length;
    int newCapacity = oldCapacity + (oldCapacity >> 1);
    if (newCapacity - minCapacity < 0)
        newCapacity = minCapacity;
    if (newCapacity - MAX_ARRAY_SIZE > 0)
        newCapacity = hugeCapacity(minCapacity);
    // minCapacity is usually close to size, so this is a win:
    elementData = Arrays.copyOf(elementData, newCapacity);
}
```

从上面的代码中可以知道，ArrayList每次扩容的倍数是之前的1.5倍

#### System.arraycopy

```java
@Test
public void test_arraycopy() {
    int[] oldArr = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
    int[] newArr = new int[oldArr.length + (oldArr.length >> 1)];

    System.arraycopy(oldArr, 0, newArr, 0, oldArr.length);

    newArr[11] = 11;
    newArr[12] = 12;
    newArr[13] = 13;
    newArr[14] = 14;

    System.out.println("数组元素：" + JSON.toJSONString(newArr));
    System.out.println("数组长度：" + newArr.length);

    /**
     * 测试结果
     *
     * 数组元素：[1,2,3,4,5,6,7,8,9,10,0,11,12,13,14]
     * 数组长度：15
     */
}
```

- 拷贝数组的过程并不复杂，主要是对 System.arraycopy 的操作。
- 上面就是把数组 oldArr 拷贝到 newArr，同时新数组的长度，采用和 ArrayList 一样的计算逻辑;oldArr.length + (oldArr.length >> 1)

#### 指定位置插入

**list.add(2, "1");**

```java
Exception in thread "main" java.lang.IndexOutOfBoundsException: Index: 2, Size: 0
 at java.util.ArrayList.rangeCheckForAdd(ArrayList.java:665)
 at java.util.ArrayList.add(ArrayList.java:477)
 at org.itstack.interview.test.ApiTest.main(ApiTest.java:14)
```

其实，一段报错提示，为什么呢?我们翻开下源码学习下

```java
public void add(int index, E element) {
    rangeCheckForAdd(index);
	// 判断是否需要扩容以及扩容操作
    ensureCapacityInternal(size + 1);  // Increments modCount!!
  // 数据拷贝迁移，把待插入位置空出来
    System.arraycopy(elementData, index, elementData, index + 1,
                     size - index);
  // 数据插入操作
    elementData[index] = element;
    size++;
}

private void rangeCheckForAdd(int index) {
        if (index > size || index < 0)
            throw new IndexOutOfBoundsException(outOfBoundsMsg(index));
    }
```

- 指定位置插入首先要判断 rangeCheckForAdd，size 的长度。
- 通过上面的元素插入我们知道，每插入一个元素，size 自增一次 size++。
- 所以即使我们申请了 10 个容量长度的 ArrayList，但是指定位置插入会依赖于 size进行判断，所以会抛出 IndexOutOfBoundsException 异常。
- 指定位置插入会将位置上的数据往后移动一位，不是覆盖数据

> size的长度是实际插入到list的数据长度，不是数组的长度

![image-20211229231950694](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112292319745.png)

指定位置插入的核心步骤包括;

1. 判断 size，是否可以插入。
2. 判断插入后是否需要扩容;ensureCapacityInternal(size + 1);
3. 数据元素迁移，把从待插入位置后的元素，顺序往后迁移
4. 给数组的指定位置赋值，也就是把待插入元素插入进来。

### 删除

![image-20211229232249001](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112292322044.png)

```java
public E remove(int index) {
    rangeCheck(index);

    modCount++;
    E oldValue = elementData(index);

    int numMoved = size - index - 1;
    if (numMoved > 0)
        System.arraycopy(elementData, index+1, elementData, index,
                         numMoved);
    elementData[--size] = null; // clear to let GC do its work

    return oldValue;
}
```

删除的过程主要包括;

1. 校验是否越界;rangeCheck(index);
2. 计算删除元素的移动长度 numMoved，并通过 System.arraycopy 自己把元素复制给自己。
3. 把结尾元素清空，null。

**这里我们做个例子:**

```java
@Test
public void test_copy_remove() {
    int[] oldArr = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

    int index = 2;
    int numMoved = 10 - index - 1;

    System.arraycopy(oldArr, index + 1, oldArr, index, numMoved);

    System.out.println("数组元素：" + JSON.toJSONString(oldArr));
}
```

**测试结果**

```java
数组元素：[1,2,4,5,6,7,8,9,10,10]
```

- 可以看到指定位置 index = 2，元素已经被删掉。
- 同时数组已经移动用元素 4 占据了原来元素 3 的位置，同时结尾的 10 还等待删除。这就是为什么 ArrayList 中有这么一句代码;`elementData[--size] = null`