### spring使用kafka

pom中添加kafka依赖

```xml
   <dependency>
            <groupId>org.springframework.kafka</groupId>
            <artifactId>spring-kafka</artifactId>
        </dependency>
```

添加kafka客户端的配置

```java
@Configuration
@EnableKafka
public class KafkaConfig{

    @Autowired
    private KafkaProperties kafkaProperties;

    @Bean
    public AdminClient adminClient() {
        Map<String, Object> configs = new HashMap<>(2);
        configs.put(AdminClientConfig.BOOTSTRAP_SERVERS_CONFIG, kafkaProperties.getBootstrapServers());
        return AdminClient.create(configs);
    }
}

```

配置文件

```yml


spring:
  kafka:
    # kafka 地址，多个用 “，”隔开
    bootstrap-servers: localhost:9092
    template:
      # 默认 topic
      default-topic: kafka_test
    # 生产者配置
    producer:
      key-serializer: org.apache.kafka.common.serialization.StringSerializer
      value-serializer: org.apache.kafka.common.serialization.StringSerializer
      retries: 3
    # 消费者配置
    consumer:
      group-id: kafka-consumer
      auto-offset-reset: latest
      key-deserializer: org.apache.kafka.common.serialization.StringDeserializer
      value-deserializer: org.apache.kafka.common.serialization.StringDeserializer
      isolation-level: read_committed
      enable-auto-commit: true
    # listener 配置，作用于 @KafkaListener
    listener:
      type: batch
      concurrency: 4
      poll-timeout: 3000

```

#### 测试topic的基础操作

```java
@SpringBootTest
public class KafkaClientTest {

    @Autowired
    private AdminClient adminClient;

    /**
     * 创建topic
     */
    @Test
    public void testCreateTopic() {
        String topicName = "first_topic";
        Integer numPartitions = 1;
        short replicationFactor = 1;

        NewTopic newTopic = new NewTopic(topicName, numPartitions, replicationFactor);
        adminClient.createTopics(Collections.singletonList(newTopic));
    }


    @Test
    public void testQueryTopic() {
        ListTopicsResult listTopicsResult = adminClient.listTopics();
        try {
            Set<String> names = listTopicsResult.names().get();
            names.forEach((name) -> System.out.print(name));
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    @Test
    public void testDeleteTopic() {
        String topicName = "first_topic";
        adminClient.deleteTopics(Collections.singletonList(topicName));
    }

}
```

#### kafka生成消息

```java
@SpringBootTest
public class ProducerTest {

    private static final Logger logger = LoggerFactory.getLogger(ProducerTest.class);
    @Autowired
    private KafkaTemplate kafkaTemplate;

    @Test
    public void testSendDefault() throws ExecutionException, InterruptedException {
        String data = "data";
        /// 发送消息至默认topic
        ListenableFuture<SendResult<String, String>> future = kafkaTemplate.sendDefault(data);
        buildCallBack(future, data);
    }

    @Test
    public void testSendTopic() throws ExecutionException, InterruptedException {
        String message = "data";
        String topicName = "first_topic";
        /// 发送消息至默认topic
        ListenableFuture<SendResult<String, String>> future = kafkaTemplate.send(topicName, message);
        buildCallBack(future, message);
    }

    private void buildCallBack(ListenableFuture<SendResult<String, String>> future, String message) {
        future.addCallback(new ListenableFutureCallback<SendResult<String, String>>() {

            @Override
            public void onFailure(Throwable throwable) {
                logger.info("消息 [{}] 发送失败，错误原因: {}", message, throwable.getMessage());
            }

            @Override
            public void onSuccess(SendResult<String, String> result) {
                logger.info("消息 [{}] 发送成功，当前 partition: {}，当前 offset: {}", message,
                        result.getRecordMetadata().partition(), result.getRecordMetadata().offset());
            }
        });
    }
}
```

#### kafka消费消息

想要消费消息，需要添加注解`KafkaListener`

```java
@Component
public class ConsumerListener {

    private static final Logger logger = LoggerFactory.getLogger(ConsumerListener.class);


    @KafkaListener(topics = "first_topic", id = "kafka")
    public void listen(String message) {
        logger.info("收到消息listen： {}", message);
    }


    @KafkaListener(topics = "first_topic", id = "kafkaconsumer1")
    public void listener(String message) {
        logger.info("收到消息listener： {}", message);
    }
}
```

使用该注解需要注意几个问题，第一配置`topic`，第二配置id，第三配置`groupId`，如果没有配置`groupId`，那么默认使用id作为groupId，当然也可以使用`idIsGroup`来决定是否使用id。

#### groupId的作用

每条消息在一个消费组中只能有一个消费者消费此消息，所以想要有多个消费者都消费该消息，那么可以使用多个不同的groupId。

具体代码可以看https://github.com/tartea/study-parent