在实际的使用当中，一个类中可能依赖了很多其他的类，这些类在spring的环境中会自动注入，不需要我们考虑依赖的问题，但是在单体测试的时候，我们测试的只有方法本身，对于注入的类不需要考虑具体的实现情况，这时候就需要使用mock去处理掉这些类。

```java
public interface DemoService {

    public String  say();
}

@Component
public class DemoServiceImpl implements DemoService{
    @Override
    public String  say() {
        System.out.println("demoServiceImpl");
        return "demoServiceImpl";
    }
}

@Component
public class DemoController {

    private DemoService demoService;

    @Autowired
    public void setDemoService(DemoService demoService){
        this.demoService = demoService;
    }

    public void sayController(){
        System.out.println("demoController");
        System.out.println(demoService.say());
    }
}

```

如果上面的代码所示，当我们测试方法`sayController`的时候，对于`DemoService`是不需要关心的，这时候只要它按照我们的想法返回固定的值就行了。

```java
//直接模拟该方法，返回想要的结果
@Test
public void test(){
  DemoService mock = mock(DemoService.class);
  when(mock.say()).thenReturn("mockDemoService");
  System.out.println(mock.say());
}
```

```java
/**
 * 
 * 使用 MockitoJUnitRunner注解后，可以自由的使用
 * @Mock注解去模拟类
 * 
 */
@RunWith(MockitoJUnitRunner.class)
public class DemoControllerTest {
    @Mock
    private DemoService demoService;
    
    
    @Test
    public void test_mock() {
        when(demoService.say()).thenReturn("mockDemoService");
        System.out.println(demoService.say());
    }
}
```

```java
//结合上述的案例，对类中的依赖可以使用下面两种方法

//使用注解@Mock
@Test
public void test_InjectMocks() {
  DemoController demoController = new DemoController();
  demoController.setDemoService(demoService);
  when(demoService.say()).thenReturn("mockDemoService");
  demoController.sayController();
}
//在测试方法中添加mock
@Test
public void test_InjectMocks1() {
  DemoController demoController = new DemoController();
  DemoService mock = mock(DemoService.class);
  demoController.setDemoService(mock);
  when(mock.say()).thenReturn("mockDemoService");
  demoController.sayController();
}
```

```java
//使用spring的管理来添加注入的方法

 @Test
 public void test_bean() {
   GenericApplicationContext ctx = new GenericApplicationContext();
   new AnnotatedBeanDefinitionReader(ctx).register(Config.class);
   ctx.refresh();

  DemoService demoService = (DemoService) ctx.getBean("demoService");
  when(demoService.say()).thenReturn("mockDemoService");
  DemoController demoController = (DemoController) ctx.getBean("demoController");
  demoController.sayController();
}

@Configuration
class Config {

    @Bean
    public DemoController demoController() {
        return new DemoController();
    }
    @Bean
    public DemoService demoService(){
        return mock(DemoService.class);
    }
}
```
