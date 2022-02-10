### 前提

------

> Why does Java's hashCode() in String use 31 as a multiplier?

![image-20211229112751023](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112291127079.png)

[https://stackoverflow.com/questions/299304/why-does-javas-hashcode-in-string-use-31-as-a-multiplier](https://stackoverflow.com/questions/299304/why-does-javas-hashcode-in-string-use-31-as-a-multiplier)

### 解释

------

这个问题其实指的就是，hashCode的计算逻辑中，为什么是31作为乘数。

```java
/**
     * Returns a hash code for this string. The hash code for a
     * {@code String} object is computed as
     * <blockquote><pre>
     * s[0]*31^(n-1) + s[1]*31^(n-2) + ... + s[n-1]
     * </pre></blockquote>
     * using {@code int} arithmetic, where {@code s[i]} is the
     * <i>i</i>th character of the string, {@code n} is the length of
     * the string, and {@code ^} indicates exponentiation.
     * (The hash value of the empty string is zero.)
     *
     * @return  a hash code value for this object.
     */
public int hashCode() {
  int h = hash;
  if (h == 0 && value.length > 0) {
    char val[] = value;

    for (int i = 0; i < value.length; i++) {
    	h = 31 * h + val[i];
    }
    hash = h;
  }
  return h;
}
```

从`String`的源码中可以看到，有一个固定值31，在for循环每次执行时进行乘积计算，循环后的公式如下：`s[0]*31^(n-1) + s[1]*31^(n-2) + ... + s[n-1]`。

那么为什么要选择31作为乘积值呢？

从上面的文章中，我们可以找到一些解释，

> The value 31 was chosen because it is an odd prime. If it were even and the multiplication overflowed, information would be lost, as multiplication by 2 is equivalent to shifting. The advantage of using a prime is less clear, but it is traditional. A nice property of 31 is that the multiplication can be replaced by a shift and a subtraction for better performance: `31 * i == (i << 5) - i`. Modern VMs do this sort of optimization automatically.

这段内容主要阐述的观点包括：

1. 31是一个奇质数，如果选择偶数会导致乘积运算时数据溢出
2. 另外在二进制中，2的5次方是32，那么也就是`31 * i == (i << 5) - i`。这主要是说乘积运算可以使用位移来提升性能，目前JVM虚拟机也会自动支持此类的优化。



> Goodrich and Tamassia computed from over 50,000 English words (formed as the union of the word lists provided in two variants of Unix) that using the constants 31, 33, 37, 39, and 41 will produce fewer than 7 collisions in each case. This may be the reason that so many Java implementations choose such constants.

这段话的意思是说使用超过5千个单词计算hashCode，这个hashCode的运算使用31、33、37、39和41作为乘积，得到碰撞结果，31被使用就很正常了。

### Hash值碰撞概率统计

根据上面得到的结论，统计出不同的乘积数对10万个单词的hash计算结果。

#### 读取单词字典表

![image-20211229115128428](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112291151466.png)

#### Hash计算函数

```java
public static Integer hashCode(String str, Integer multiplier) {
        int hash = 0;
        for (int i = 0; i < str.length(); i++) {
            hash = multiplier * hash + str.charAt(i);
        }
        return hash;
    }
```

#### Hash碰撞概率计算

```java
/**
     * 计算Hash碰撞概率
     */
    private static RateInfo hashCollisionRate(Integer multiplier, List<Integer> hashCodeList) {
        int maxHash = hashCodeList.stream().max(Integer::compareTo).get();
        int minHash = hashCodeList.stream().min(Integer::compareTo).get();

        int collisionCount = (int) (hashCodeList.size() - hashCodeList.stream().distinct().count());
        double collisionRate = (collisionCount * 1.0) / hashCodeList.size();

        return new RateInfo(maxHash, minHash, multiplier, collisionCount, collisionRate);
    }
    public static List<RateInfo> collisionRateList(Set<String> strList, Integer... multipliers) {
        List<RateInfo> rateInfoList = new ArrayList<>();
        for (Integer multiplier : multipliers) {
            List<Integer> hashCodeList = new ArrayList<>();
            for (String str : strList) {
                Integer hashCode = hashCode(str, multiplier);
                hashCodeList.add(hashCode);
            }
            rateInfoList.add(hashCollisionRate(multiplier, hashCodeList));
        }
        return rateInfoList;
    }
```

这里记录了最大hash和最小hash值，以及最终返回碰撞数量的统计结果。

#### 单元测试

```java
    private Set<String> words;

    @Before
    public void before() {
        "abc".hashCode();
        // 读取文件，103976个英语单词库.txt
        words = FileUtil.readWordList("/Users/jiaxiansheng/develop/interview/interview-03/103976个英语单词库.txt");
    }

    @Test
    public void test_collisionRate() {
        System.out.println("单词数量：" + words.size());
        List<RateInfo> rateInfoList = HashCode.collisionRateList(words, 2, 3, 5, 7, 17, 31, 32, 33, 39, 41, 199);
        for (RateInfo rate : rateInfoList) {
            System.out.println(String.format("乘数 = %4d, 最小Hash = %11d, 最大Hash = %10d, 碰撞数量 =%6d, 碰撞概率 = %.4f%%", rate.getMultiplier(), rate.getMinHash(), rate.getMaxHash(), rate.getCollisionCount(), rate.getCollisionRate() * 100));
        }
    }
```

#### 测试结果

![image-20211229115624688](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112291156726.png)

![image-20211229115704947](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112291157982.png)

以上就是不同的乘数下的hash碰撞结果图表展示：

1. 乘数是2时，hash的取值范围比较小，基本是堆积到一个范围内了，后面内容会看到这块的展示
2. 乘数是 3、5、7、17 等，都有较大的碰撞概率
3. 乘数是 31 的时候，碰撞的概率已经很小了，基本稳定。
4. 顺着往下看，你会发现 199 的碰撞概率更小，这就相当于一排奇数的茅坑量多，自然会减少碰撞。但这个范围值已经远超过 int 的取值范围了，如果用此数作为乘数，又返回 int 值，就会丢失数据信息。

### Hash值散列分布

除了以上看到哈希值在不同乘数的一个碰撞概率后，关于散列表也就是 hash， 还有一个非常重要的点，那就是要尽可能的让数据散列分布。只有这样才能减少 hash 碰撞次数。

那么怎么看散列分布呢?如果我们能把 10 万个 hash 值铺到图表上，形成的一张 图，就可以看出整个散列分布。但是这样的图会比较大，当我们缩小看后，就成 一个了大黑点。所以这里我们采取分段统计，把 2 ^ 32 方分 64 个格子进行存 放，每个格子都会有对应的数量的 hash 值，最终把这些数据展示在图表上。

#### 哈希值分段存放

```java
    public static Map<Integer, Integer> hashArea(List<Integer> hashCodeList) {
        Map<Integer, Integer> statistics = new LinkedHashMap<>();
        int start = 0;
        for (long i = 0x80000000; i <= 0x7fffffff; i += 67108864) {
            long min = i;
            long max = min + 67108864;
            // 筛选出每个格子里的哈希值数量，java8流统计；https://bugstack.cn/itstack-demo-any/2019/12/10/%E6%9C%89%E7%82%B9%E5%B9%B2%E8%B4%A7-Jdk1.8%E6%96%B0%E7%89%B9%E6%80%A7%E5%AE%9E%E6%88%98%E7%AF%87(41%E4%B8%AA%E6%A1%88%E4%BE%8B).html
            int num = (int) hashCodeList.parallelStream().filter(x -> x >= min && x < max).count();
            statistics.put(start++, num);
        }
        return statistics;
    }

    public static Map<Integer, Integer> hashArea(Set<String> strList, Integer multiplier){
        List<Integer> hashCodeList = new ArrayList<>();
        for (String str : strList) {
            Integer hashCode = hashCode(str, multiplier);
            hashCodeList.add(hashCode);
        }
        return hashArea(hashCodeList);
    }
```

这个过程主要统计int取值范围内，每个哈希值存放到不同格子里的数量

#### 单元测试

```java
    /**
     * 返回此字符串的哈希码。 String对象的哈希码计算如下
     *        s[0]*31^(n-1) + s[1]*31^(n-2) + ... + s[n-1]
     *
     * 使用int算术，其中s[i]是字符串的第i个字符， n是字符串的长度， ^表示求幂。 （空字符串的哈希值为零。）
     * 返回：
     * 此对象的哈希码值。
     */
    @Test
    public void test_hashArea() {
        System.out.println(HashCode.hashArea(words, 2).values());
        System.out.println(HashCode.hashArea(words, 7).values());
        System.out.println(HashCode.hashArea(words, 31).values());
        System.out.println(HashCode.hashArea(words, 32).values());
        System.out.println(HashCode.hashArea(words, 199).values());
    }
```

#### 统计图表

![image-20211229120354702](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112291203749.png)

以上是一个堆积百分比统计图，可以看到下方是不同乘数下的，每个格子里的数据统计，除了199不能用以外，31的散列结果相对来说比较均匀。

![image-20211229120608526](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202112291206583.png)

乘数是199是不能用的散列结果，但是他的数据是更加分散的，从图上可以看到有两个小山包，但是因为数据区间问题会有数据丢失问题，所以不能选择。

### 文件

[103976个英语单词库.txt](https://images-1258301517.cos.ap-nanjing.myqcloud.com/file/103976%E4%B8%AA%E8%8B%B1%E8%AF%AD%E5%8D%95%E8%AF%8D%E5%BA%93.txt)

[HashCode散列分布](https://images-1258301517.cos.ap-nanjing.myqcloud.com/file/HashCode%E6%95%A3%E5%88%97%E5%88%86%E5%B8%83.xlsx)