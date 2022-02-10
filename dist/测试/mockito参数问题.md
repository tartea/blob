在一个方法中模拟另外一个方法的时候，正常情况下mock方法会根据方式传递的参数是否相同去判断是否mock这个方法。

```java
public interface DemoService {
    public String  sayHello(String str);
}
@Component
public class DemoServiceImpl implements DemoService{

    @Override
    public String sayHello(String str) {
        System.out.println(str);
        return "demoServiceImpl" + str;
    }
}

@Component
public class DemoController {

    private DemoService demoService;

    @Autowired
    public void setDemoService(DemoService demoService){
        this.demoService = demoService;
    }

    public void sayHello(String str){
        System.out.println("demoController");
        System.out.println(demoService.sayHello(str));
    }
}

```

```java
//如果mock.sayHello(str)和demoController.sayHello(str)方法调用的字符串是相同的字符串
//那么返回的结果就是想要的结果
// demoController
// mockDemoService
@Test
public void test_hello_InjectMocks() {
  DemoController demoController = new DemoController();
  DemoService mock = mock(DemoService.class);
  demoController.setDemoService(mock);
  String str = "hello";
  when(mock.sayHello(str)).thenReturn("mockDemoService");
  demoController.sayHello(str);
}

//使用下面的方法，会发现返回的结果中，mock.sayHello(str)返回的是null
//demoController
//null
//这是由于模拟方法中的参数要和实际调用该方法是的参数是相同的地址，否则无法使用mock的方法
@Test
public void test_hello_InjectMocks_1() {
  DemoController demoController = new DemoController();
  DemoService mock = mock(DemoService.class);
  demoController.setDemoService(mock);
  String str = "hello";
  when(mock.sayHello(str)).thenReturn("mockDemoService");
  demoController.sayHello("mock controller");
}
```

**解决办法**

```
  //模拟的方法使用any()，从官方的解释来看，该方法可以匹配任何内容，包括空值和可变参数，
  //对于原始类型，请使用anyChar()系列或anyChar() isA(Class)或any(Class)
  @Test
  public void test_hello_InjectMocks_way() {
    DemoController demoController = new DemoController();
    DemoService mock = mock(DemoService.class);
    demoController.setDemoService(mock);
    String str = "hello";
    when(mock.sayHello(any())).thenReturn("mockDemoService");
    demoController.sayHello("mock controller");
  }
```

```java
// 创建自定义的参数匹配器
@Test
public void test_hello_InjectMocks_way1() {
  DemoController demoController = new DemoController();
  DemoService mock = mock(DemoService.class);
  demoController.setDemoService(mock);
  String str = "hello";
  when(mock.sayHello(argThat(new ArgumentMatcher<String>() {
    @Override
    public boolean matches(String argument) {
      return true;
    }
  }))).thenReturn("mockDemoService");
  demoController.sayHello("mock controller");
}
```

