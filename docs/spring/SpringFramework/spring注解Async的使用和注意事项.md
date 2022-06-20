### 使用

添加注解，启动异步，如果想要使用**@Async**注解，那么必须在启动类或者config文件中添加注解**@EnableAsync**

```java
@Configuration
@EnableAsync // 开启 @Async 的支持
public class AsyncConfig {
}

@Async
public Integer execute01Async() {
	return sleepService.execute01();
}

public Integer execute01() {
	logger.info("[execute01]");
	sleep(10);
	return 1;
}
```

```java
    @Test
    public void task() {
        long now = System.currentTimeMillis();
        logger.info("[task02][开始执行]");

        asyncService.execute01Async();
        asyncService.execute02Async();

        logger.info("[task02][结束执行，消耗时长 {} 毫秒]", System.currentTimeMillis() - now);
    }
```

从上面的测试结果可以看到，主线程结束的时间比子线程结束的时间要早,这是因为对于使用async注解的方法会使用异步的方式去处理。

对于该注解，spring底层默认使用的线程池是**SimpleAsyncTaskExecutor**，该线程池是不会重用的，默认每次调用都会创建一个新的线程

```
TaskExecutor implementation that fires up a new Thread for each task, executing it asynchronously.
Supports limiting concurrent threads through the "concurrencyLimit" bean property. By default, the number of concurrent threads is unlimited.
NOTE: This implementation does not reuse threads! Consider a thread-pooling TaskExecutor implementation instead, in particular for executing a large number of short-lived tasks
```

从**SimpleAsyncTaskExecutor**
的注释中可以清楚的了解到该线程池的线程数是无限的，所以在实际使用的过程中会导致任务的堆积，或者导致内存溢出，针对线程创建问题，SimpleAsyncTaskExecutor提供了限流机制，通过concurrencyLimit属性来控制开关，当concurrencyLimit>
=0时开启限流机制，默认关闭限流机制即concurrencyLimit=-1，当关闭情况下，会不断创建新的线程来处理任务。基于默认配置，SimpleAsyncTaskExecutor并不是严格意义的线程池，达不到线程复用的功能。

### 自定义线程池

自定义线程池有三种方式：

- 重新实现接口AsyncConfigurer

- 继承AsyncConfigurerSupport

- 配置由自定义的TaskExecutor替代内置的任务执行器

  ```java
  @Configuration
  @EnableAsync // 开启 @Async 的支持
  public class AsyncConfig {
  
      public static final String EXECUTOR_ONE_BEAN_NAME = "executor-one";
      public static final String EXECUTOR_TWO_BEAN_NAME = "executor-two";
  
      @Configuration
      public static class ExecutorOneConfiguration {
  
          @Bean(name = EXECUTOR_ONE_BEAN_NAME + "-properties")
          @Primary
          @ConfigurationProperties(prefix = "spring.task.execution-one") // 读取 spring.task.execution-one 配置到 TaskExecutionProperties 对象
          public TaskExecutionProperties taskExecutionProperties() {
              return new TaskExecutionProperties();
          }
  
          @Bean(name = EXECUTOR_ONE_BEAN_NAME)
          public ThreadPoolTaskExecutor threadPoolTaskExecutor() {
              // 创建 TaskExecutorBuilder 对象
              TaskExecutorBuilder builder = createTskExecutorBuilder(this.taskExecutionProperties());
              // 创建 ThreadPoolTaskExecutor 对象
              return builder.build();
          }
  
      }
  
      @Configuration
      public static class ExecutorTwoConfiguration {
  
          @Bean(name = EXECUTOR_TWO_BEAN_NAME + "-properties")
          @ConfigurationProperties(prefix = "spring.task.execution-two") // 读取 spring.task.execution-two 配置到 TaskExecutionProperties 对象
          public TaskExecutionProperties taskExecutionProperties() {
              return new TaskExecutionProperties();
          }
  
          @Bean(name = EXECUTOR_TWO_BEAN_NAME)
          public ThreadPoolTaskExecutor threadPoolTaskExecutor() {
              // 创建 TaskExecutorBuilder 对象
              TaskExecutorBuilder builder = createTskExecutorBuilder(this.taskExecutionProperties());
              // 创建 ThreadPoolTaskExecutor 对象
              return builder.build();
          }
  
      }
  
      private static TaskExecutorBuilder createTskExecutorBuilder(TaskExecutionProperties properties) {
          // Pool 属性
          TaskExecutionProperties.Pool pool = properties.getPool();
          TaskExecutorBuilder builder = new TaskExecutorBuilder();
          builder = builder.queueCapacity(pool.getQueueCapacity());
          builder = builder.corePoolSize(pool.getCoreSize());
          builder = builder.maxPoolSize(pool.getMaxSize());
          builder = builder.allowCoreThreadTimeOut(pool.isAllowCoreThreadTimeout());
          builder = builder.keepAlive(pool.getKeepAlive());
          // Shutdown 属性
          TaskExecutionProperties.Shutdown shutdown = properties.getShutdown();
          builder = builder.awaitTermination(shutdown.isAwaitTermination());
          builder = builder.awaitTerminationPeriod(shutdown.getAwaitTerminationPeriod());
          // 其它基本属性
          builder = builder.threadNamePrefix(properties.getThreadNamePrefix());
  //        builder = builder.customizers(taskExecutorCustomizers.orderedStream()::iterator);
  //        builder = builder.taskDecorator(taskDecorator.getIfUnique());
          return builder;
      }
  
  }
  ```

  ```yml
  spring.task.execution-one.thread-name-prefix=task-one-
  spring.task.execution-one.pool.core-size=18
  spring.task.execution-one.pool.max-size=20
  spring.task.execution-one.pool.keep-alive=60s
  spring.task.execution-one.pool.queue-capacity=200
  spring.task.execution-one.pool.allow-core-thread-timeout=true
  spring.task.execution-one.shutdown.await-termination=true
  spring.task.execution-one.shutdown.await-termination-period=60
  spring.task.execution-two.thread-name-prefix=task-two-
  spring.task.execution-two.pool.core-size=8
  spring.task.execution-two.pool.max-size=20
  spring.task.execution-two.pool.keep-alive=60s
  spring.task.execution-two.pool.queue-capacity=200
  spring.task.execution-two.pool.allow-core-thread-timeout=true
  spring.task.execution-two.shutdown.await-termination=true
  spring.task.execution-two.shutdown.await-termination-period=60
  ```

  ```java
  //在需要异步处理的方法中，添加注解，同时添加线程池的Bean名称
  @Async(AsyncConfig.EXECUTOR_ONE_BEAN_NAME)
  public Future<Integer> execute01AsyncWithFuture() {
  	System.out.println(Thread.currentThread().getName());
    //如果有需要返回的值，可以使用AsyncResult.forValue去处理
  	return AsyncResult.forValue(sleepService.execute01());
  }
  ```

  ```java
  @Test
  public void task1() throws ExecutionException, InterruptedException {
  	long now = System.currentTimeMillis();
  	logger.info("[task02][开始执行]");
  
  	Future<Integer> future = asyncService.execute01AsyncWithFuture();
  	Future<Integer> future1 = asyncService.execute02AsyncWithFuture();
  
  	System.out.println(future.get());
  	System.out.println(future1.get());
  
  	logger.info("[task02][结束执行，消耗时长 {} 毫秒]", System.currentTimeMillis() - now);
  }
  ```

  
