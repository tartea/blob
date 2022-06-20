### StringBuilder 比 String 快吗?

-----

#### String

```java
    public void test_03() {
        long startTime = System.currentTimeMillis();
        String str = "";
        for (int i = 0; i < 1000000; i++) {
            str += i;
        }
        System.out.println("String 耗时：" + (System.currentTimeMillis() - startTime) + "毫秒");
    }
```

#### StringBuilder

```java
    @Test
    public void test_04() {
        long startTime = System.currentTimeMillis();
        StringBuilder str = new StringBuilder();
        for (int i = 0; i < 1000000; i++) {
            str.append(i);
        }
        System.out.println("StringBuilder 耗时" + (System.currentTimeMillis() - startTime) + "毫秒");
    }
```

#### StringBuffer

```java
    @Test
    public void test_05() {
        long startTime = System.currentTimeMillis();
        StringBuffer str = new StringBuffer();
        for (int i = 0; i < 1000000; i++) {
            str.append(i);
        }
        System.out.println("StringBuffer 耗时" + (System.currentTimeMillis() - startTime) + "毫秒");
    }

```

综上，分别使用了 String、StringBuilder、StringBuffer，做字符串链接操作 (100 个、1000 个、1 万个、10 万个、100 万个)，记录每种方式的耗时。最终汇 总图表如下;

![image-20211230220125054](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112302201102.png)

从上图可以得出以下结论;

- String 字符串链接是耗时的，尤其数据量大的时候，简直没法使用了。这是做 实验，基本也不会有人这么干!
- StringBuilder、StringBuffer，因为没有发生多线程竞争也就没有锁升级，所以两个类耗时几乎相同，当然在单线程下更推荐使用 StringBuilder 。

### StringBuilder 比 String 快， 为什么?

------

```java
String str = "";
for (int i = 0; i < 10000; i++) {
	str += i; 
}
```

这段代码就是三种字符串拼接方式，最慢的一种。不是说这种+加的符号，会被 优化成 StringBuilder 吗，那怎么还慢?

确实会被 JVM 编译期优化，但优化成什么样子了呢，先看下字节码指令;`javap -c ApiTest.class`

![image-20211230220522070](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112302205108.png)

一看指令码，这不是在循环里(if_icmpgt)给我 new 了 StringBuilder 了吗， 怎么还这么慢呢?再仔细看，其实你会发现，这 new 是在循环里吗呀，我们把这 段代码写出来再看看;

```java
String str = "";
for (int i = 0; i < 10000; i++) {
	str = new StringBuilder().append(str).append(i).toString(); 
}
```

现在再看这段代码就很清晰了，所有的字符串链接操作，都需要实例化一次 StringBuilder，所以非常耗时。并且你可以验证，这样写代码耗时与字符串直接 链接是一样的。 所以把 StringBuilder 提到上一层 for 循环外更快。

### String 源码分析

------

#### 初始化

```java
    @Test
    public void test_01() {
        String str_01 = "abc";
        System.out.println("默认方式：" + str_01);

        String str_02 = new String(new char[]{'a', 'b', 'c'});
        System.out.println("char方式：" + str_02);

        String str_03 = new String(new int[]{0x61, 0x62, 0x63}, 0, 3);
        System.out.println("int方式：" + str_03);

        String str_04 = new String(new byte[]{0x61, 0x62, 0x63});
        System.out.println("byte方式：" + str_04);

        char c = str_01.charAt(0);

    }
```

以上这些方式都可以初始化，并且最终的结果是一致的，abc。如果说初始化的 方式没用让你感受到它是数据结构，那么 str_01.charAt(0);呢，只要你往源码 里一点，就会发现它是 O(1) 的时间复杂度从数组中获取元素，所以效率也是非
常高，源码如下;

```java
public char charAt(int index) {
    if ((index < 0) || (index >= value.length)) {
        throw new StringIndexOutOfBoundsException(index);
    }
    return value[index];
}
```

#### 不可变

```java
public final class String
    implements java.io.Serializable, Comparable<String>, CharSequence {
    /** The value is used for character storage. */
    private final char value[];
}
```

从源码中可以看到，String 的类和用于存放字符串的方法都用了 final 修饰， 也就是创建了以后，这些都是不可变的。

#### 案例

```
    @Test
    public void test_00() {
        String str_01 = "abc";
        String str_02 = "abc" + "def";
        String str_03 = str_01 + "def";

        String intern = str_01.intern();

        System.out.println(str_01 == intern);
    }
```

对于上面的代码，到底初始化了几个对象呢？

反编译

```java
  public void test_00();
    Code:
       0: ldc           #2                  // String abc
       2: astore_1
       3: ldc           #3                  // String abcdef
       5: astore_2
       6: new           #4                  // class java/lang/StringBuilder
       9: dup
      10: invokespecial #5                  // Method java/lang/StringBuilder."<init>":()V
      13: aload_1
      14: invokevirtual #6                  // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      17: ldc           #7                  // String def
      19: invokevirtual #6                  // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      22: invokevirtual #8                  // Method java/lang/StringBuilder.toString:()Ljava/lang/String;
      25: astore_3
      26: aload_1
      27: invokevirtual #9                  // Method java/lang/String.intern:()Ljava/lang/String;
      30: astore        4
      32: getstatic     #10                 // Field java/lang/System.out:Ljava/io/PrintStream;
      35: aload_1
      36: aload         4
      38: if_acmpne     45
      41: iconst_1
      42: goto          46
      45: iconst_0
      46: invokevirtual #11                 // Method java/io/PrintStream.println:(Z)V
      49: return

```

- str_01 = "abc"，指令码:0: ldc，创建了一个对象。
- str_02 = "abc" + "def"，指令码:3: ldc // String abcdef，得益于 JVM 编译期的优化，两个字符串会进行相连，创建一个对象存储。
- str_03 = str_01 + "def"，指令码:invokevirtual，这个就不一样了，它需要把两个字符串相连，会创建 StringBuilder 对象，直至最后 toString:()操作，共创建了三个对象。

所以，我们看到，字符串的创建是不能被修改的，相连操作会创建出新对象。

#### intern()

```java
    @Test
    public void test_000() {
        String str_1 = new String("ab");
        String str_2 = new String("ab");
        String str_3 = "ab";

        System.out.println(str_1 == str_2);
        System.out.println(str_1 == str_2.intern());
        System.out.println(str_1.intern() == str_2.intern());
        System.out.println(str_1 == str_3);
        System.out.println(str_1.intern() == str_3);
//        运行结果
//        false
//        false
//        true
//        false
//        true
    }
```

**源码**

```java
    /**
     * Returns a canonical representation for the string object.
     * <p>
     * A pool of strings, initially empty, is maintained privately by the
     * class {@code String}.
     * <p>
     * When the intern method is invoked, if the pool already contains a
     * string equal to this {@code String} object as determined by
     * the {@link #equals(Object)} method, then the string from the pool is
     * returned. Otherwise, this {@code String} object is added to the
     * pool and a reference to this {@code String} object is returned.
     * <p>
     * It follows that for any two strings {@code s} and {@code t},
     * {@code s.intern() == t.intern()} is {@code true}
     * if and only if {@code s.equals(t)} is {@code true}.
     * <p>
     * All literal strings and string-valued constant expressions are
     * interned. String literals are defined in section 3.10.5 of the
     * <cite>The Java&trade; Language Specification</cite>.
     *
     * @return  a string that has the same contents as this string, but is
     *          guaranteed to be from a pool of unique strings.
     */
    public native String intern();
```

先用图来解释

![image-20211230221403054](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112302214097.png)

看图说话，如下;

1. 先说 ==，基础类型比对的是值，引用类型比对的是地址。另外，equal 比对的是 哈希值。
2. 两个 new 出来的对象，地址肯定不同，所以是 false。
3. intern()，直接把值推进了常量池，所以两个对象都做了 intern() 操作后，比对是常量池里的值。
4. str_3 = "ab"，赋值，JVM 编译器做了优化，不会重新创建对象，直接引用常量池里的值。所以 str_1.intern() == str_3，比对结果是 true。

> intern会直接从常量池中获取数据，如果常量池中不存在，那么就初始化一个

### StringBuilder 源码分析

------

#### 初始化

```java
new StringBuilder();
new StringBuilder(16); 
new StringBuilder("abc");
```

这几种方式都可以初始化，你可以传一个初始化容量，也可以初始化一个默认的 字符串。它的源码如下;

```java
    public StringBuffer() {
        super(16);
    }
     AbstractStringBuilder(int capacity) {
        value = new char[capacity];
    }
```

定睛一看，这就是在初始化数组呀!那是不操作起来跟使用 ArrayList 似的呀!

#### 添加元素

```java
    @Test
    public void test_07() {
        StringBuffer stringBuffer = new StringBuffer();

        stringBuffer.append("a");
        stringBuffer.append("b");
        stringBuffer.append("c");
    }
```

```java
@Override
public synchronized StringBuffer append(String str) {
    toStringCache = null;
    super.append(str);
    return this;
}
   public AbstractStringBuilder append(String str) {
        if (str == null)
            return appendNull();
        int len = str.length();
        ensureCapacityInternal(count + len);
        str.getChars(0, len, value, count);
        count += len;
        return this;
    }
```

这里包括了容量检测、元素拷贝、记录 count 数量。

##### 扩容操作

```java
/**
 * For positive values of {@code minimumCapacity}, this method
 * behaves like {@code ensureCapacity}, however it is never
 * synchronized.
 * If {@code minimumCapacity} is non positive due to numeric
 * overflow, this method throws {@code OutOfMemoryError}.
 */
private void ensureCapacityInternal(int minimumCapacity) {
    // overflow-conscious code
    if (minimumCapacity - value.length > 0) {
        value = Arrays.copyOf(value,
                newCapacity(minimumCapacity));
    }
}
    private int newCapacity(int minCapacity) {
        // overflow-conscious code
        int newCapacity = (value.length << 1) + 2;
        if (newCapacity - minCapacity < 0) {
            newCapacity = minCapacity;
        }
        return (newCapacity <= 0 || MAX_ARRAY_SIZE - newCapacity < 0)
            ? hugeCapacity(minCapacity)
            : newCapacity;
    }
```

如上，StringBuilder，就跟操作数组的原理一样，都需要检测容量大小，按需扩 容。扩容的容量是 n * 2 + 2，另外把原有元素拷贝到新新数组中。

##### 填充元素

```java
    str.getChars(0, len, value, count);
    public void getChars(int srcBegin, int srcEnd, char dst[], int dstBegin) {
        if (srcBegin < 0) {
            throw new StringIndexOutOfBoundsException(srcBegin);
        }
        if (srcEnd > value.length) {
            throw new StringIndexOutOfBoundsException(srcEnd);
        }
        if (srcBegin > srcEnd) {
            throw new StringIndexOutOfBoundsException(srcEnd - srcBegin);
        }
        System.arraycopy(value, srcBegin, dst, dstBegin, srcEnd - srcBegin);
    }
```

添加元素的方式是基于 System.arraycopy 拷贝操作进行的，这是一个本地方法.

#### toString()

既然 stringBuilder 是数组，那么它是怎么转换成字符串的呢? `stringBuilder.toString();`

```java
    public synchronized String toString() {
        if (toStringCache == null) {
            toStringCache = Arrays.copyOfRange(value, 0, count);
        }
        return new String(toStringCache, true);
    }
```

其实需要用到它是 String 字符串的时候，就是使用 String 的构造函数传递数 组进行转换的，这个方法在我们上面讲解 String 的时候已经介绍过。

### StringBuffer 源码分析

------

StringBuffer 与 StringBuilder，API 的使用和底层实现上基本一致，维度不同 的是 StringBuffer 加了 synchronized 锁，所以它是线程安全的。源码如下;

```java
    @Override
    public synchronized StringBuffer append(String str) {
        toStringCache = null;
        super.append(str);
        return this;
    }
```

那么，synchronized 不是重量级锁吗，JVM 对它有什么优化呢? 其实为了减少获得锁与释放锁带来的性能损耗，从而引入了偏向锁、轻量级锁、 重量级锁来进行优化，它的进行一个锁升级。