Zuul是spring cloud中的微服务网关。网关：是一个网络整体系统中的前置门户入口。请求首先通过网关，进行路径的路由，定位到具体的服务节点上。

Zuul是一个微服务网关，首先是一个微服务。也是会在Eureka注册中心中进行服务的注册和发现。也是一个网关，请求应该通过Zuul来进行路由。

Zuul网关不是必要的。是推荐使用的。

使用Zuul，一般在微服务数量较多（多于10个）的时候推荐使用，对服务的管理有严格要求的时候推荐使用，当微服务权限要求严格的时候推荐使用

### 网关作用

网关有以下几个作用：

- 统一入口：未全部为服务提供一个唯一的入口，网关起到外部和内部隔离的作用，保障了后台服务的安全性。
- 鉴权校验：识别每个请求的权限，拒绝不符合要求的请求。
- 动态路由：动态的将请求路由到不同的后端集群中。
- 减少客户端与服务端的耦合：服务可以独立发展，通过网关层来做映射

![image-20220212144640756](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202202121446788.png)

### 代码实现

![image-20220212145614779](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202202121456813.png)

启动类上添加注解`EnableZuulProxy`保证当前服务有网管的作用

配置完成后就可以直接访问服务了

先使用原有的ip地址http://localhost:8888/restServer访问服务

![image-20220212145738299](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202202121457333.png)

通过网关访问服务

![image-20220212145800595](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202202121458624.png)

分解上面的访问地址，可以看到中间是服务的名称，后面是服务的接口，这样可以达到同样的效果

zuul默认代理了eureka中所有的服务，所以我们可以通过去修改zuul的配置文件去忽略一些服务的方法，也可以修改访问服务的格式

#### 修改访问方式

```yaml
zuul:
  routes:
    study-rest:
      path: /restService/**
      serviceId: study-rest
```

修改后重新启动服务，就可以通过新的访问方式去访问服务了

![image-20220212150334417](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202202121503444.png)

### 注解解释

因为使用的是`@EnableZuulProxy`注解，所以zuul和hystrix做了一些关联

我们可以在网关中添加一些hystrix的配置

```yaml
hystrix:
  command:
    default:
      execution:
        isolation:
          strategy: thread
          thread:
            timeoutInMilliseconds: 100
```

配置完hystrix后再次访问服务，你会在控制台发现一个警告

![image-20220212150811368](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202202121508398.png)

因为hystrix的timeoutInMilliseconds要大于ribbon的ribbonTimeout，而ribbonTimeout的超时时间为4000，所以hystrix的超时时间要大于该时间

![image-20220212150906417](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202202121509446.png)

### 优化配置

我们可以针对某一个服务添加一些配置，通过添加配置来优化该服务

![image-20220212151201594](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202202121512626.png)

### zuul网关访问失败

zuul对于服务访问失败有处理方法，在低版本和高版本中接口不一样，低版本为ZuulFallbackProvider，高版本为FallbackProvider

```java
import org.springframework.http.client.ClientHttpResponse;

/**
 * Provides fallback when a failure occurs on a route.
 *
 * @author Ryan Baxter
 * @author Dominik Mostek
 */
public interface FallbackProvider {

   /**
    * The route this fallback will be used for.
    * @return The route the fallback will be used for.
    */
   String getRoute();

   /**
    * Provides a fallback response based on the cause of the failed execution.
    * @param route The route the fallback is for
    * @param cause cause of the main method failure, may be <code>null</code>
    * @return the fallback response
    */
   ClientHttpResponse fallbackResponse(String route, Throwable cause);

}
```

#### 访问失败的实现

```java
@Component
public class ZuulFallbackMethod implements FallbackProvider {


    public ClientHttpResponse fallbackResponse(String route, Throwable cause) {
        if (cause != null && cause.getCause() != null) {
            String reason = cause.getCause().getMessage();
        }
        return fallbackResponse();
    }
  
    /**
     * 使用*可以匹配所有的服务
     *
     * @return
     */
    public String getRoute() {
        return "*";
    }

    public ClientHttpResponse fallbackResponse() {
        return new ClientHttpResponse() {
            public HttpStatus getStatusCode() throws IOException {
                return HttpStatus.OK;
            }

            public int getRawStatusCode() throws IOException {
                return 200;
            }

            public String getStatusText() throws IOException {
                return "OK";
            }

            public void close() {

            }

            public InputStream getBody() throws IOException {
                return new ByteArrayInputStream("The service is unavailable.".getBytes());
            }

            public HttpHeaders getHeaders() {
                HttpHeaders headers = new HttpHeaders();
                headers.setContentType(MediaType.APPLICATION_JSON);
                return headers;
            }
        };
    }

}
```

停止rest服务，然后通过http://localhost:9003/restService/restServer访问服务，会发现页面返回的时候方式失败时候的结果

![image-20220212160224075](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202202121602116.png)