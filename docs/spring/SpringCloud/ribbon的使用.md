### 原理

ribbon是一个负载均衡器，它可以让原本直接调用某种服务变成根据某种算法（如轮询，随机访问）去访问多个服务，当然我们也可以自己定义轮询算法

![image-20220212134350158](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202202121343254.png)

在我们常规使用`RestTemplate`,我们需要指定ip和端口，不然访问不了服务，但是在使用注解`@LoadBalanced`以后就可以直接根据注册中心上的负载名称来访问服务了。这种情况下就可以增加服务的提供者，实现负载访问了。

### 代码实现

提供两个服务的提供者`study-rest`和`study-rest-server`,服务名称保持一致，都叫做`study-rest`，提供一个可以访问的服务

```java
@RequestMapping("restServer")
public String rest(){
  	return "this is a rest server1";
}
@RequestMapping("restServer")
public String rest(){
    return "this is a rest server2";
}
```

服务启动后，可以清楚的在eureka的注册中心看到

![image-20220212140138283](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202202121401312.png)

#### 实现ribbon

```java
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.ClientHttpRequestFactory;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

@Configuration
public class RestTemplateConfig {

    /**
     * LoadBalanced 让使用该注解得方法拥有负载均衡的能力，所有使用LoadBalanced注解的方法都会
     * 被拦截器LoadBalancerInterceptor拦截，然后根据调用的服务名称在LoadBalancerClient中调用服务
     *
     * @return
     * @date 2020/12/22
     */
    @Bean("restTemplate")
    @LoadBalanced
    public RestTemplate restTemplate(@Qualifier("simpleClientHttpRequestFactory") ClientHttpRequestFactory factory) {
        return new RestTemplate(factory);//在Spring容器中注入RestTemplate对象
    }

    @Bean("ipTemplate")
    public RestTemplate ipTemplate(@Qualifier("simpleClientHttpRequestFactory") ClientHttpRequestFactory factory) {
        return new RestTemplate(factory);//在Spring容器中注入RestTemplate对象
    }


    @Bean
    public ClientHttpRequestFactory simpleClientHttpRequestFactory() {
        //初始化RestTemplate对象需要的Factory工厂类，biang注入到Spring容器中
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setReadTimeout(50000);//读取反馈超时时间5000ms
        factory.setConnectTimeout(15000);//连接超时时间15000ms
        return factory;
    }
}
```

提供两个`RestTemplate`bean实例，其中一个添加了注解`@LoadBalanced`，保证restTemplate具有负载的功能

#### 测试负载能力

```java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;

@RestController
public class RibbonController {


    @Autowired
    @Qualifier("restTemplate")
    private RestTemplate restTemplate;

    @Autowired
    @Qualifier("ipTemplate")
    private RestTemplate ipTemplate;


    /**
     * 通过ip和端口访问服务
     * @return
     */
    @RequestMapping("restByIp")
    public String restByIp(){
        return "this is IP Access   " + ipTemplate.getForObject("http://localhost:8888/restServer", String.class);
    }


    /**
     * 通过负载名称访问服务
     * @return
     */
    @RequestMapping("restByLoadBalancing")
    public String restByLoadBalancing(){
        return "this is load balancing   " + restTemplate.getForObject("http://study-rest/restServer", String.class);
    }
}
```

通过上面的两个方法可以清楚的看到，`restByIp`方法只能通过ip:port的方法去访问，这样服务的提供者只能有一个，但是`restByLoadBalancing`方法是通过服务提供者的名称去访问的，那么服务提供者可以有多个。

#### 测试

浏览器访问http://localhost:9001/restByLoadBalancing，不断的刷新，可以发现浏览器响应的内容不断的在服务提供者之间切换。

![image-20220212140758515](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202202121407545.png)

![image-20220212140805154](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202202121408180.png)

#### 解释

为什么添加了`@LoadBalanced`注解后，restTemplate就可以通过服务名称访问了呢？

通过源码可以知道，通过`@LoadBalanced`调用的方法可以被拦截器`LoadBalancerInterceptor`拦截，然后将服务传递给类`RibbonLoadBalancerClient`，

```java
public <T> T execute(String serviceId, LoadBalancerRequest<T> request, Object hint)
      throws IOException {
   ILoadBalancer loadBalancer = getLoadBalancer(serviceId);
   Server server = getServer(loadBalancer, hint);
   if (server == null) {
      throw new IllegalStateException("No instances available for " + serviceId);
   }
   RibbonServer ribbonServer = new RibbonServer(serviceId, server,
         isSecure(server, serviceId),
         serverIntrospector(serviceId).getMetadata(server));

   return execute(serviceId, ribbonServer, request);
}
```

通过上面的源码可以知道，ribbon通过服务名称从注册中心中获取到服务的提供者，然后通过轮询算法从服务的提供者中选择一个，然后调用服务

### 自定义配置

```java
public class RibbonClientConfiguration {

   /**
    * Ribbon client default connect timeout.
    */
   public static final int DEFAULT_CONNECT_TIMEOUT = 1000;

   /**
    * Ribbon client default read timeout.
    */
   public static final int DEFAULT_READ_TIMEOUT = 1000;

   /**
    * Ribbon client default Gzip Payload flag.
    */
   public static final boolean DEFAULT_GZIP_PAYLOAD = true;

   @RibbonClientName
   private String name = "client";

   // TODO: maybe re-instate autowired load balancers: identified by name they could be
   // associated with ribbon clients

   @Autowired
   private PropertiesFactory propertiesFactory;

   @Bean
   @ConditionalOnMissingBean
   public IClientConfig ribbonClientConfig() {
      DefaultClientConfigImpl config = new DefaultClientConfigImpl();
      config.loadProperties(this.name);
      config.set(CommonClientConfigKey.ConnectTimeout, DEFAULT_CONNECT_TIMEOUT);
      config.set(CommonClientConfigKey.ReadTimeout, DEFAULT_READ_TIMEOUT);
      config.set(CommonClientConfigKey.GZipPayload, DEFAULT_GZIP_PAYLOAD);
      return config;
   }

   @Bean
   @ConditionalOnMissingBean
   public IRule ribbonRule(IClientConfig config) {
      if (this.propertiesFactory.isSet(IRule.class, name)) {
         return this.propertiesFactory.get(IRule.class, config, name);
      }
      ZoneAvoidanceRule rule = new ZoneAvoidanceRule();
      rule.initWithNiwsConfig(config);
      return rule;
   }

   @Bean
   @ConditionalOnMissingBean
   public IPing ribbonPing(IClientConfig config) {
      if (this.propertiesFactory.isSet(IPing.class, name)) {
         return this.propertiesFactory.get(IPing.class, config, name);
      }
      return new DummyPing();
   }

   @Bean
   @ConditionalOnMissingBean
   @SuppressWarnings("unchecked")
   public ServerList<Server> ribbonServerList(IClientConfig config) {
      if (this.propertiesFactory.isSet(ServerList.class, name)) {
         return this.propertiesFactory.get(ServerList.class, config, name);
      }
      ConfigurationBasedServerList serverList = new ConfigurationBasedServerList();
      serverList.initWithNiwsConfig(config);
      return serverList;
   }

   @Bean
   @ConditionalOnMissingBean
   public ServerListUpdater ribbonServerListUpdater(IClientConfig config) {
      return new PollingServerListUpdater(config);
   }

   @Bean
   @ConditionalOnMissingBean
   public ILoadBalancer ribbonLoadBalancer(IClientConfig config,
         ServerList<Server> serverList, ServerListFilter<Server> serverListFilter,
         IRule rule, IPing ping, ServerListUpdater serverListUpdater) {
      if (this.propertiesFactory.isSet(ILoadBalancer.class, name)) {
         return this.propertiesFactory.get(ILoadBalancer.class, config, name);
      }
      return new ZoneAwareLoadBalancer<>(config, rule, ping, serverList,
            serverListFilter, serverListUpdater);
   }

   @Bean
   @ConditionalOnMissingBean
   @SuppressWarnings("unchecked")
   public ServerListFilter<Server> ribbonServerListFilter(IClientConfig config) {
      if (this.propertiesFactory.isSet(ServerListFilter.class, name)) {
         return this.propertiesFactory.get(ServerListFilter.class, config, name);
      }
      ZonePreferenceServerListFilter filter = new ZonePreferenceServerListFilter();
      filter.initWithNiwsConfig(config);
      return filter;
   }

   @Bean
   @ConditionalOnMissingBean
   public RibbonLoadBalancerContext ribbonLoadBalancerContext(ILoadBalancer loadBalancer,
         IClientConfig config, RetryHandler retryHandler) {
      return new RibbonLoadBalancerContext(loadBalancer, config, retryHandler);
   }

   @Bean
   @ConditionalOnMissingBean
   public RetryHandler retryHandler(IClientConfig config) {
      return new DefaultLoadBalancerRetryHandler(config);
   }

   @Bean
   @ConditionalOnMissingBean
   public ServerIntrospector serverIntrospector() {
      return new DefaultServerIntrospector();
   }

   @PostConstruct
   public void preprocess() {
      setRibbonProperty(name, DeploymentContextBasedVipAddresses.key(), name);
   }

   static class OverrideRestClient extends RestClient {

      private IClientConfig config;

      private ServerIntrospector serverIntrospector;

      protected OverrideRestClient(IClientConfig config,
            ServerIntrospector serverIntrospector) {
         super();
         this.config = config;
         this.serverIntrospector = serverIntrospector;
         initWithNiwsConfig(this.config);
      }

      @Override
      public URI reconstructURIWithServer(Server server, URI original) {
         URI uri = updateToSecureConnectionIfNeeded(original, this.config,
               this.serverIntrospector, server);
         return super.reconstructURIWithServer(server, uri);
      }

      @Override
      protected Client apacheHttpClientSpecificInitialization() {
         ApacheHttpClient4 apache = (ApacheHttpClient4) super.apacheHttpClientSpecificInitialization();
         apache.getClientHandler().getHttpClient().getParams().setParameter(
               ClientPNames.COOKIE_POLICY, CookiePolicy.IGNORE_COOKIES);
         return apache;
      }

   }

}
```

查看ribbon的配置类，可以清楚的看到很多的方法都使用了`@ConditionalOnMissingBean`注解，那么我们可以通过自定义配置来覆盖原本的配置。

比如ribbon客户端配置，轮询算法等

#### 轮询算法

![image-20220212143011577](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202202121430619.png)

从上面的图片中可以清楚的看到。ribbon已经实现了四种负载方法，我们可以通过选择其中一个来覆盖它原有的功能，当然也可以自己实现负载的方法

```java
import com.netflix.loadbalancer.IRule;
import com.netflix.loadbalancer.RandomRule;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RibbonRuleConfig {

    /**
     * 1、随机分配流量
     */
    @Bean
    public IRule ribbonRule() {
        return new RandomRule();
    }

    /**
     * 2、访问请求最少的地址
     */
//    @Bean
//    public IRule ribbonRule() {
//        return new BestAvailableRule();
//    }
    /**
     * 3、轮询的策略
     */
//    @Bean
//    public IRule ribbonRule() {
//        return new RoundRobinRule();
//    }

}
```

如果将上面的配置类放在可以扫描的路径下，那么会变成一个全局的配置类，所以如果想针对某一个服务提供者提供上面的配置，那么需要将配置类放在无法扫描到的路径下，然后通过配置以下参数来使用

![image-20220212144044912](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202202121440955.png)

