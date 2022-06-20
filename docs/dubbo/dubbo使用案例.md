![image-20220325153731548](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202203251537687.png)

从上面的图可以了解到，dubbo项目的建立一般需要四个模块（当然也可以缩减）

### dubbo-model

```java
public class User implements Serializable {
    private static final long serialVersionUID = -7518658808692242651L;

    private String name;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    @Override
    public String toString() {
        return "User{" +
                "name='" + name + '\'' +
                '}';
    }
}

```

### dubbo-api

#### pom文件

```xml
<dependencies>
    <dependency>
        <groupId>org.tartea</groupId>
        <artifactId>dubbo-model</artifactId>
        <version>0.0.1-SNAPSHOT</version>
    </dependency>
</dependencies>
```

```java
public interface ProviderService {

    String sayHello(String word);

    String sayHello(User user);
}
```

### dubbo-provider

#### pom文件

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>2.5.10</version>
        <relativePath/> <!-- lookup parent from repository -->
    </parent>
    <groupId>org.tartea</groupId>
    <artifactId>dubbo-provider</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    <name>dubbo-provider</name>
    <description>Demo project for Spring Boot</description>
    <properties>
        <java.version>1.8</java.version>
        <dubbo.version>2.7.5</dubbo.version>
        <zookeeper.version>3.4.14</zookeeper.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter</artifactId>
        </dependency>

        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>

        <dependency>
            <groupId>org.tartea</groupId>
            <artifactId>dubbo-api</artifactId>
            <version>0.0.1-SNAPSHOT</version>
        </dependency>

        <!-- dubbo-start依赖 -->
        <dependency>
            <groupId>org.apache.dubbo</groupId>
            <artifactId>dubbo-spring-boot-starter</artifactId>
            <version>${dubbo.version}</version>
        </dependency>
        <!--zookeeper 注册中心客户端引入 使用的是curator客户端 -->
        <dependency>
            <groupId>org.apache.dubbo</groupId>
            <artifactId>dubbo-dependencies-zookeeper</artifactId>
            <version>${dubbo.version}</version>
            <type>pom</type>
            <exclusions>
                <exclusion>
                    <artifactId>slf4j-log4j12</artifactId>
                    <groupId>org.slf4j</groupId>
                </exclusion>
            </exclusions>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>

</project>

```

#### 配置文件

```yml
##服务器端口号
server:
  port: 7001
##dubbo 注册到注册中心的名称
dubbo:
  application:
    name: test-provider
  ##采用协议方式和端口号
  protocol:
    ## 常用协议：dubbo,http,webService等
    name: dubbo
    ## 发布dubbo端口号为20880
    port: 20881
  registry:
    ## dubbo注册中心地址 zookeeper地址
    address: zookeeper://127.0.0.1:2181
  scan:
    ## 实现类扫包范围(可以省略，dubbo会自动扫 带了@Service的类)
    base-packages: org.tartea.service.impl
```

```java
import org.springframework.beans.factory.annotation.Value;
import org.apache.dubbo.config.annotation.Service;
import org.tartea.entity.User;
import org.tartea.service.ProviderService;


/**
 *服务提供者实现类
 */
@Service
public class ProviderServiceImpl implements ProviderService {

    @Value("${dubbo.protocol.port}")
    private String dubboPort;

    // 1.dubbo服务发布的时候采用dubbo 注解方式,使用 dubbo @Service注解 进行发布服务
    // 2.dubbo 提供的 @Service 将该接口的实现注册到注册中心上去
    // 3.spring 的 @Service 将该类注入到spring容器中
    @Override
    public String sayHello(String word) {
        System.out.println("订单服务调用会员服务...dubbo服务端口号：" + dubboPort);
        return "订单服务调用会员服务...dubbo服务端口号：" + dubboPort;
    }

    @Override
    public String sayHello(User user) {
        System.out.println("订单服务调用会员服务...dubbo服务端口号：" + dubboPort + user.toString());
        return "订单服务调用会员服务...dubbo服务端口号：" + dubboPort;
    }
}
```

> 这里需要注意@Service注解，它导入的并不是spring下的，而是dubbo包下面的

### dubbo-sonsumer

#### pom文件

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>2.5.10</version>
        <relativePath/> <!-- lookup parent from repository -->
    </parent>
    <groupId>org.tartea</groupId>
    <artifactId>dubbo-consumer</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    <name>dubbo-consumer</name>
    <description>Demo project for Spring Boot</description>
    <properties>
        <java.version>1.8</java.version>
        <dubbo.version>2.7.5</dubbo.version>
        <zookeeper.version>3.4.14</zookeeper.version>
    </properties>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>

        <dependency>
            <groupId>org.tartea</groupId>
            <artifactId>dubbo-api</artifactId>
            <version>0.0.1-SNAPSHOT</version>
        </dependency>
    
        <dependency>
            <groupId>org.apache.dubbo</groupId>
            <artifactId>dubbo-spring-boot-starter</artifactId>
            <version>${dubbo.version}</version>
        </dependency>

        <!-- dubbo的zookeeper依赖 -->
        <dependency>
            <groupId>org.apache.dubbo</groupId>
            <artifactId>dubbo-dependencies-zookeeper</artifactId>
            <version>${dubbo.version}</version>
            <type>pom</type>
            <exclusions>
                <exclusion>
                    <artifactId>slf4j-log4j12</artifactId>
                    <groupId>org.slf4j</groupId>
                </exclusion>
            </exclusions>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>

</project>
```

#### 配置文件

```yml
server:
  port: 7000
spring:
  application:
    name: test-consumer
# dubbo 相关配置
dubbo:
  application:
    name: order-consumer
  registry:
    address: zookeeper://127.0.0.1:2181
```

#### 测试方法

```java
import org.apache.dubbo.config.annotation.Reference;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.tartea.service.ProviderService;

@SpringBootTest
public class ApiTest {

    @Reference
    private ProviderService providerService;

    @Test
    public void test(){
        String result = providerService.sayHello("tartea");
        System.out.println(result);
    }
}
```

> 这里想要调用dubbo接口，需要引入注解@Reference

以上就是一个简单的使用dubbo的案例，想要看具体的可以参考[git@github.com:tartea/study-parent.git](git@github.com:tartea/study-parent.git)

### 问题

上面的实现是都是依赖`dubbo-api`模块去操作了，有没有想过`dubbo-provider`和`dubbo-consumer`之间没有依赖过相同的模块，即大家都定义自己的接口，只是接口中的内容是相同的。

### 实现

将`dubbo-provider`和`dubbo-consumer`模块中的依赖的`dubbo-api`都删除，然后在每个模块中定义自己的`ProviderService`方法，只是方法中的内容是相同的，然后启动`ApiTest`
，可以发现依然可以调用

该操作可以证明能否调用和是否依赖相同的模块没有任何的关系，只要保证接口名称和方法相同就可以调用到了

具体的可以参考[git@github.com:tartea/study-parent.git](git@github.com:tartea/study-parent.git)的分支`dubbo/v1.0.0`

### dubbo-admin

为了可以清楚的了解到哪些dubbo服务被注册和消费了，需要一个可视化界面，这时候dubbo-admin就派上用场了

```shell
git clone git@github.com:apache/dubbo-admin.git
cd dubbo-admin
mvn clean package -Dmaven.test.skip=true
```

修改dubbo-admin-server下的配置文件

```yml
#--- 配置zookeeper相关信息，主要配置ip和port，保证与zookeeper的监听端口一致 -----
admin.registry.address=zookeeper:``//127``.0.0.1:2181
admin.config-center=zookeeper:``//127``.0.0.1:2181
admin.metadata-report.address=zookeeper:``//127``.0.0.1:2181

# 配置root用户登录管理端的密码
admin.root.user.name=root
admin.root.user.password=root
```

改完一个使用`mvn clean package -Dmaven.test.skip=true`重新构建

然后启动dubbo-admin-distribution/target/dubbo-admin-0.4.0.jar

```shell
java -jar dubbo-admin-0.4.0.jar
```

启动成功后就可以使用localhost:8080去访问了，当然也可以在启动脚本中添加`-Dserver.port=7100`或者修改配置文件去改变端口号