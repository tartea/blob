### 为什么使用validator

`javax.validation`的一系列注解可以帮我们完成参数校验,免去繁琐的串行校验

不然我们的代码就像下面这样:

```java
//  http://localhost:8080/api/user/save/serial

    /**
     * 走串行校验
     *
     * @param userVO
     * @return
     */
    @PostMapping("/save/serial")
    public Object save(@RequestBody UserVO userVO) {
        String mobile = userVO.getMobile();

        //手动逐个 参数校验~ 写法
        if (StringUtils.isBlank(mobile)) {
            return RspDTO.paramFail("mobile:手机号码不能为空");
        } else if (!Pattern.matches("^[1][3,4,5,6,7,8,9][0-9]{9}$", mobile)) {
            return RspDTO.paramFail("mobile:手机号码格式不对");
        }

        //抛出自定义异常等~写法
        if (StringUtils.isBlank(userVO.getUsername())) {
            throw new BizException(Constant.PARAM_FAIL_CODE, "用户名不能为空");
        }

        // 比如写一个map返回
        if (StringUtils.isBlank(userVO.getSex())) {
            Map<String, Object> result = new HashMap<>(5);
            result.put("code", Constant.PARAM_FAIL_CODE);
            result.put("msg", "性别不能为空");
            return result;
        }
        //.........各种写法 ...
        userService.save(userVO);
        return RspDTO.success();
    }

```

什么是`javax.validation`

JSR303 是一套JavaBean参数校验的标准，它定义了很多常用的校验注解，我们可以直接将这些注解加在我们JavaBean的属性上面(面向注解编程的时代)，就可以在需要校验的时候进行校验了,在SpringBoot中已经包含在starter-web中,再其他项目中可以引用依赖,并自行调整版本:

```xml
  <!--jsr 303-->
        <dependency>
            <groupId>javax.validation</groupId>
            <artifactId>validation-api</artifactId>
            <version>1.1.0.Final</version>
        </dependency>
        <!-- hibernate validator-->
        <dependency>
            <groupId>org.hibernate</groupId>
            <artifactId>hibernate-validator</artifactId>
            <version>5.2.0.Final</version>
        </dependency>
```

![image-20220114215611080](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202201142156132.png)

![image-20220114215644027](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202201142156058.png)

此处只列出Hibernate Validator提供的大部分验证约束注解，请参考hibernate validator官方文档了解其他验证约束注解和进行自定义的验证约束注解定义。

### 使用方法

#### 声明参数

```java
 @PostMapping("save")
    public String save(@RequestBody @Validated User user) {
        return user.toString();
    }
```

#### 对参数添加注解

```java
import org.hibernate.validator.constraints.Length;
import javax.validation.constraints.*;
import java.io.Serializable;
import java.util.Date;
/**
 * @Author: jiawenhao
 * @Date: 2022-01-14  21:26
 */
public class User implements Serializable {

    private static final long serialVersionUID = 1L;

    /*** 用户ID*/
    @NotNull(message = "用户id不能为空")
    private Long userId;

    /**
     * 用户名
     */
    @NotBlank(message = "用户名不能为空")
    @Length(max = 20, message = "用户名不能超过20个字符")
    @Pattern(regexp = "^[\\u4E00-\\u9FA5A-Za-z0-9\\*]*$", message = "用户昵称限制：最多20字符，包含文字、字母和数字")
    private String username;

    /**
     * 手机号
     */
    @NotBlank(message = "手机号不能为空")
    @Pattern(regexp = "^[1][3,4,5,6,7,8,9][0-9]{9}$", message = "手机号格式有误")
    private String mobile;

    /**
     * 性别
     */
    private String sex;

    /**
     * 邮箱
     */
    @NotBlank(message = "联系邮箱不能为空")
    @Email(message = "邮箱格式不对")
    private String email;

    /**
     * 密码
     */
    private String password;

    /*** 创建时间 */
    @Future(message = "时间必须是将来时间")
    private Date createTime;


    public Long getUserId() {
        return userId;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public String getMobile() {
        return mobile;
    }

    public void setMobile(String mobile) {
        this.mobile = mobile;
    }

    public String getSex() {
        return sex;
    }

    public void setSex(String sex) {
        this.sex = sex;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public Date getCreateTime() {
        return createTime;
    }

    public void setCreateTime(Date createTime) {
        this.createTime = createTime;
    }

    @Override
    public String toString() {
        return "User{" +
                "userId=" + userId +
                ", username='" + username + '\'' +
                ", mobile='" + mobile + '\'' +
                ", sex='" + sex + '\'' +
                ", email='" + email + '\'' +
                ", password='" + password + '\'' +
                ", createTime=" + createTime +
                '}';
    }
}
```

#### 测试

![image-20220114215900997](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202201142159037.png)

> 因为使用的是`@RequestBody`，所以参数应该是json类型，所以postman要设置为JSON，请求的方式使用的是post方法

在放松请求后，可以在idea的控制台打印出错误的消息。

![image-20220114220152998](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202201142201033.png)

由此我们可以清楚的知道，validator成功拦截错误的数据，但是这样的错误显示方式在实际业务开发中是无法使用的。

因此需要添加全局的异常拦截器

#### 错误拦截器

`@RestControllerAdvice`是一个全局的异常拦截器，我们可以在里面获取一些常常出现的异常，然后将这些异常转变成前段可以了解的信息，但是我们也可以自定义一些异常。

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger logger = LoggerFactory.getLogger(GlobalExceptionHandler.class);
      /**
     * 方法参数校验
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public String handleMethodArgumentNotValidException(MethodArgumentNotValidException e) {
        logger.error(e.getMessage(), e);
        return e.getBindingResult().getFieldError().getDefaultMessage();
    }

    @ExceptionHandler(MissingServletRequestParameterException.class)
    public String handleDefaultHandlerExceptionResolver(MissingServletRequestParameterException e) {
        logger.error(e.getMessage(), e);
        return e.getMessage();
    }
    @ExceptionHandler(ConstraintViolationException.class)
    public String handleConstraintViolationException(ConstraintViolationException e) {
        logger.error(e.getMessage(), e);
        return e.getMessage();
    }
}
```

在添加完上述的全局异常拦截器后，我们再次请求。

![image-20220114220546143](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202201142205179.png)

这时候可以清楚的看到，错误信息已经在控制台显示了。

### 请求方法中验证参数

上面我们已经对实体中的参数进行了验证，但是有时候我们的请求接口中可能只有一个`string`，这时候是不可能在定义一个实体的，那么这时候该如何处理呢？

#### 定义controller验证

![image-20220114220945789](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202201142209825.png)

在Controller上添加注解`@Validator`

#### 对参数添加验证逻辑

```java
@PostMapping("update")
public String update(@RequestParam @NotEmpty(message = "名称不能为空") @Pattern(regexp = "^[1][3,4,5,6,7,8,9][0-9]{9}$", message = "手机号格式有误") String username) {
    return username;
}
```

对参数添加验证，同时一个参数上可以同时添加多个验证注解

### 分组

![image-20220114221124233](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202201142211274.png)

通过查看一个注解的源码可以了解到，有一个参数`groups`，可以通过该参数让验证只在指定的地方生效。

比如保存一个`userId`字段，该字段只有在初始创建的时候才需要验证，在更新的时候其实是不需要验证，那么就可以通过`groups`去区分这些使用情况。

#### 使用方法

**定义分组接口，注意接口需要继承javax.validation.groups.Default**

```java
import javax.validation.groups.Default;

public interface Update extends Default {
}

import javax.validation.groups.Default;

public interface Create extends Default {
}
```

#### 添加验证注解

```java
import org.hibernate.validator.constraints.Length;
import javax.validation.constraints.NotBlank;
import java.io.Serializable;

public class Blob implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 用户名
     */
    @NotBlank(message = "用户名不能为空")
    @Length(max = 10, message = "用户名不能超过10个字符", groups = {Update.class})
    private String username;

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    @Override
    public String toString() {
        return "Blob{" +
                "username='" + username + '\'' +
                '}';
    }
}
```

在字段上添加注解，同时添加变了`groups`

#### 在调用接口添加验证

```java
    @PostMapping("blogCreate")
    public String blogCreate(@RequestBody @Validated(value = {Create.class}) Blob blob) {
        return blob.toString();
    }

    @PostMapping("blogUpdate")
    public String blogUpdate(@RequestBody @Validated(Update.class) Blob blob) {
        return blob.toString();
    }
```

可以看到上面两个方法分别在`@Validated`添加了权限

#### 测试

![image-20220114222625252](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202201142226292.png)

![image-20220114222634521](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202201142226558.png)

从上面的测试结果可以看出，`update`对输入的字符进行了验证，而`create`直接忽略了验证。