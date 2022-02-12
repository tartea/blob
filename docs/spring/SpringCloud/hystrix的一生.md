### 服务熔断的原因

#### 雪崩效应

长链路调用过程中, A->B->C.... 假设链路上 C 出现了调用缓慢->B也会延迟->A也会延迟,堵住的 A 请求会消耗占用系统的线程、IO 等资源. 当对 A 服务的请求越来越多，占用的计算机资源越来越多的时候，会导致系统瓶颈出现，造成其他的请求同样不可用，最终导致业务系统崩溃，这种现象称为雪崩效应。

![image-20220211143939291](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202202111439322.png)

#### 熔断机制 - 用于解决雪崩效应的问题

当请求失败(超时或者其他异常)次数超过预设值时，熔断器自动打开. 

  这时所有经过这个熔断器的请求都会直接返回失败(不会堵住A请求)，并没有真正到达所依赖的服务上。

### Hystrix实现服务熔断与降级

#### 实现原理

Hystrix 是一种开关装置，类似于熔断保险丝。在消费者端安装一个 Hystrix 熔断器，当 Hystrix 监控到某个服务发生故障后熔断器会开启，将此服务访问链路断开。 

不过 Hystrix 并不会将该服务的消费者阻塞，或向消费者抛出异常，而是向消费者返回一个符合预期的备选响应（FallBack）。 通过 Hystrix 的熔断与降级功能，避免了服务雪崩的发生，同时也考虑到了用户体验。故 Hystrix 是系统的一种防御机制。

#### 服务降级

服务降级指的是在如果发生故障的时候，可以使用次一级的方法来临时解决问题，在hystrix中使用的是`falbackMethod`来解决降级的问题。

##### 代码实现

- 在启动类上添加`@EnableCircuitBreaker`注解
- 在方法上添加注解`@HystrixCommand`
- 添加配置，如果不添加配置的话，默认的超时时间为1秒钟

```yaml
hystrix:
  command:
    default:
      execution:
        timeoutInMilliseconds: 10000
        isolation:
          strategy: THREAD
          thread:
            timeoutInMilliseconds: 5000
```

```java
@RestController
public class FallbackMethodController {


    @RequestMapping("getUserName")
    public String getUserName() {
        try {
            //模拟停顿时间
            Thread.sleep(10000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        return "this is method";
    }


    @RequestMapping("getUserNameFallBack")
    @HystrixCommand(
            fallbackMethod = "getFallbackMethod"// 服务降级方法
    )
    public String getUserNameFallBack(@RequestParam String timeout) {
        System.out.println("---------------");
        try {
            //模拟停顿时间
            Thread.sleep(Integer.parseInt(timeout));
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        return "this is a success method";
    }

    /**
     * fall back method
     *
     * @return
     */
    private String getFallbackMethod(String timeout) {

        return "this is a fallback method";
    }


}
```

```java
@SpringBootTest
@RunWith(SpringRunner.class)
class FallbackMethodControllerTest {

    @Autowired
    private WebApplicationContext webApplicationContext;

    private MockMvc mockMvc;

    @BeforeEach
    private void setUp() {
        //使用上下文构建MockMvc
        mockMvc = MockMvcBuilders.webAppContextSetup(webApplicationContext).build();

    }

    @Test
    void getUserName() throws Exception {
        //执行请求（使用GET请求，RESTful接口）
        MvcResult mvcResult = mockMvc.perform(MockMvcRequestBuilders.get("/getUserName").accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        //获取返回编码
        int status = mvcResult.getResponse().getStatus();
        //获取返回结果
        String content = mvcResult.getResponse().getContentAsString();
        //断言，判断返回编码是否正确
        Assert.assertEquals("this is method", content);

    }

    @Test
    void getUserNameFallBack() throws Exception {

        //请求时间为3秒钟，没有超时
        MvcResult mvcResult = mockMvc.perform(MockMvcRequestBuilders.get("/getUserNameFallBack").param("timeout","3000").accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        //获取返回编码
        int status = mvcResult.getResponse().getStatus();
        //获取返回结果
        String content = mvcResult.getResponse().getContentAsString();
        //断言，判断返回编码是否正确
        Assert.assertEquals("this is a success method", content);
    }
    @Test
    void getUserNameFallBackTimeOut() throws Exception {

        //请求时间为6秒钟，请求超时，走fall back method
        MvcResult mvcResult = mockMvc.perform(MockMvcRequestBuilders.get("/getUserNameFallBack").param("timeout","6000").accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        //获取返回编码
        int status = mvcResult.getResponse().getStatus();
        //获取返回结果
        String content = mvcResult.getResponse().getContentAsString();
        //断言，判断返回编码是否正确
        Assert.assertEquals("this is a fallback method", content);
    }
}
```

从上面的配置可以看到`hystrix`的熔断时间为5秒中，在没有添加`@HystrixCommand`注解的时候，是默默等待方法执行完的，但是在添加注解后，如果请求的时间超过熔断的时间，那么会调用fallbackMethod。

如果从源码的角度来看注解`HystrixCommand`的话，可以看到该 注解使用的是aop增强的方式。

<img src="https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202202111604852.png" alt="image-20220211160426818" style="zoom:50%;" />

### 隔离策略

为了对请求的数量进行一定的限制，hystrix做了隔离策略，主要的目的是：防止服务熔断，防止服务雪崩

#### 隔离的类型

- **线程隔离 thread (默认)**：系统会**创建一个依赖线程池**，为**每个依赖请求分配一个独立的线程**，而每个依赖所拥有的线程数量是有上限的。当对该依赖的调用 请求数量达到上限后再有请求，则该请求阻塞。所以对某依赖的并发量取决于为该依赖 所分配的线程数量。

  适用于: **耗时长, 高吞吐量**, 例如读数据库, 大计算.

- **信号量隔离**：对依赖的调用所使用的线程仍为请求线程，即不会为依赖请求再新创建新的线程。但系统会为每种依赖分配一定数量的信号量，而每个依赖请求分配一个信号号。当对该依赖的调用请求数量达到上限后再有请求，则该请求阻塞。所以对某依赖的并发 量取决于为该依赖所分配的信号数量。

  适用于:**耗时短, 低延迟**, 例如高频读取缓存

![image-20220211160714820](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202202111607852.png)

**设置方式**

```properties
hystrix.command.default.execution.isolation.strategy=thread 
hystrix.command.default.execution.isolation.strategy=semaphore
```

**执行隔离其它属性**

```properties
# 若采用线程执行隔离策略, 开启线程的执行时间超时
hystrix.command.default.execution.timeout.enabled = (true) 
# 若采用线程执行隔离策略, 执行线程超时时限长度
hystrix.command.default.execution.isolation.thread.timeoutInMilliseconds = (1000ms) 
# 当线程执行超时时是否中断线程的执行
hystrix.command.default.execution.isolation.thread.interruptOnTimeout = (true) 
# 请求取消，当前执行线程是否结束
hystrix.command.default.execution.isolation.thread.interruptOnCancel = (false) 
# 若采用信号量执行隔离策略，则可通过以下属性修改信号量的数量
hystrix.command.default.execution.isolation.semaphore.maxConcurrentRequests = 
```

**熔断器属性**

```properties
# 当前应用是否开启熔断器功能
hystrix.command.default.circuitBreaker.enabled = (true)
# 在窗口期内(一个时间段内) 收到的请求数量超过该设置的数量后，将开启熔断器
hystrix.command.default.circuitBreaker.requestVolumeThreshold = (20) 
# 窗口期时间
hystrix.command.default.circuitBreaker.sleepWindowInMilliseconds = (5000ms) 
# 当请求的错误率高于该百分比时，开启熔断器。
hystrix.command.default.circuitBreaker.errorThresholdPercentage = (50 即为50%) 
# 强制开启熔断器, 熔断所有请求
hystrix.command.default.circuitBreaker.forceOpen = (false) 
# 强制关闭所有熔断器, 通过所有请求
hystrix.command.default.circuitBreaker.forceClosed = (false)
```

**熔断时间设置**

 对于最终触发熔断超时时长的原因 , 除了 hystrix 的 timeoutInMilliseconds 自生有关 如果 ribbon 的 ReadTimeout 超时也会抛出读超时, 此时也会触发熔断. 如果有Zuul 设置超时时长原理类似

```yaml
feign:
  client:
    config:
      default:
        connectTimeout: 6000 # 指定Feign客户端连接提供者的超时时限
        readTimeout: 6000 # 指定Feign客户端连接上提供者后，向提供者进行提交请求，从提交时刻开始，到接收到响应，这个时段的超时时限

ribbon:
  ReadTimeout: 5000   #负载均衡超时时间，默认值5000
  ConnectTimeout: 2000 #ribbon请求连接的超时时间，默认值2000

hystrix:
  command: # 全局配置
    default:
      execution:
        isolation:
          thread:
            timeoutInMilliseconds: 4000 # 断路器超时时间，默认1000ms
  XxxApi#apiMethod(String,Integer,Boolean):  # 特定接口配置局配置 (括号内填写参数类型)
    execution:    
      timeout:
        enabled: true # 开启线程的执行时间超时
          isolation:
            thread:
              timeoutInMilliseconds: 6000  # 断路器超时时间，默认1000ms 
```

1. ribbon 中的 connectTimeout连接时长 和 ReadTimeout读取时长, **ribbon: 会被  feign:client 配置覆盖掉**

2. hystrix 中的 timeoutInMilliseconds熔断时间 **优先级: 特定接口>全局通用**, 特定配置可以在 yml或者通过@HystrixProperty(name="execution.isolation.thread.timeoutInMilliseconds", value="4000") 进行配置

3. 假设此接口开启了hystrix熔断器的前提下, **ReadTimeout 和 timeoutInMilliseconds 取时间短的进行读超时**, 读超时会触发熔断

4. 开启熔断器的条件

5. - 启动标签包含 @SpringCloudApplication 或者 @EnableCircuitBreaker 支持熔断器
   - feign:hystrix:enabled: true(默认false不开启 ) OpenFeign全局接口开启熔断器, 使得fegin中的fallback标签生效
   - hystrix:command:default:execution:timeout:enabled: true 使得@HystrixCommand(fallbackMethod = "回退方法")生效

6. ribbon还有**MaxAutoRetries对当前实例的重试次数**,**MaxAutoRetriesNextServer对切换实例的重试次数**, 如果ribbon的ReadTimeout超时,或者ConnectTimeout连接超时,会进行重试操作

   通常 **timeoutInMilliseconds 需要配置的比ReadTimeout长,ReadTimeout比ConnectTimeout长**,否则还未重试,就熔断了

   为了确保重试机制的正常运作,理论上（以实际情况为准）建议**hystrix的超时时间为:(1 + MaxAutoRetries + MaxAutoRetriesNextServer) \* ReadTimeout**

如果想更深入的了解hystrix的机制，可以从源码中了解，具体的位置为

![image-20220211161253908](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202202111612963.png)