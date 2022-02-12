Feign是一个声明式 WebService 客户端，使用Feign能够让编写Web Service 客户端更加简单，它的使用方法是定义一个接口，然后在上面添加注解，同时也支持JAX-RS标准的注解。Feign也支持可插拔式的编码器和解码器。

　　Spring Cloud 对 Fiegn 进行了封装，使其支持了Spring MVC 标准注解和HttpMessageConverts。Feign可以与Eureka和Ribbon组合使用以支持负载均衡。

### 代码实现

```java
@FeignClient("study-rest")
public interface IRestServer {

    @RequestMapping("/restServer")
    String feignRestServer();

}
```

针对restServer添加一个接口，然后在需要的地方直接调用接口的方法就可以调用远程方法了

```java
@RestController
public class FeignController {


    @Autowired
    private IRestServer restServer;


    @RequestMapping("restFeign")
    public String restFeign(){
        return restServer.feignRestServer();
    }
}
```

feign使用起来是很简单的，但是需要考虑一些问题，如超时，重试

### 自定义配置

为了保证配置只针对指定的服务有效，所以将类放在扫描不到的地方

```java
public class FeignConfig {

    /**
     * 设置重试
     *
     * @return
     */
    @Bean
    public Retryer feignRetryer() {
        Retryer retryer = new Retryer.Default(1000, 10000, 10);
        return retryer;
    }
}
```

```java
@FeignClient(value = "study-rest",configuration = FeignConfig.class)
public interface IRestServer {


    @RequestMapping("/restServer")
    String feignRestServer();

}
```

可以看到上述的类中配置了重试机制，所以在我们调用方法的时候，可以先将服务停掉，然后会发现服务一直在访问中，在我们将服务启动后，会发现浏览器返回了正确的结果

> 测试的时候需要注意一个问题，那就是feign需要从注册中心获取服务，所以在启动停止服务的时候，需要注意间隔

feign的调用也是有超时时间这些配置的，我们可以在yml中配置这些内容

```yaml
feign:
  client:
    config:
      default:
        connectTimeout: 10000
  hystrix:
    enabled: true
```

> feign使用的是hystrix和ribbon，而且hystrix是在外层的，所以hystrix的的超时时间要大于ribbon的超时时间，所以当同时配置feign的conneTimeout参数值要大于ribbon的参数值。