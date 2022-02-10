### 准备工作

1. 下载编译包

   [下载地址，选择zip文件](https://hg.openjdk.java.net/jdk/jdk12/file/1ddf9a99e4ad)

   ![image-20211016130444937](https://gitee.com/gluten/images/raw/master/images/202110212148268.png)

2. 准备bootstrap jdk

   bootstrap jdk指的是编译jdk需要的环境，一般是比编译的jdk低一个版本

   [下载地址](http://planetone.online/downloads/java/jdk-11.0.9_osx-x64_bin.tar.gz)

   如果你本地没有jdk环境的话，可以使用安装配置到本地，如果存在其他版本的jdk的话，那就没必要安装当前版本了

   安装的时候有具体的教学方法

3. 编译环境

   ```
   macOS Big Sur 11.6
   brew install autoconf
   brew install freetype
   ```

   安装xcode，一般本地存在```xcode-select```,但是在编译jdk的过程中可能会出错，这里可以先不安装**xcode**，待后面编译的时候报错在编译


​	如果出现说scode-select路径不对的情况下，执行如下命令

```
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
```

使用上述命令报错的话，可以将报错的目录删除，注意删除后可能会影响其他软件的使用，从appstore重新安装xcode

### 编译

在编译之前，可以先看下**doc**目录下的build.html文件，这个文件主要是编译的帮助文档，避免踩坑

这里在编译之前，需要注意的就是bootstrap jdk，如果之前没有安装低一个版本的jdk也没有关系，这里可以设置临时当前环境，只在当前控制台有效

```
export JAVA_HOME=/Users/jiaxiansheng/develop/jdk/jdk-11.0.9/Contents/Home
```

#### 编译命令

```
bash configure --enable-debug --with-jvm-variants=server --enable-dtrace --with-boot-jdk=/Users/jiaxiansheng/develop/jdk/jdk-11.0.9/Contents/Home
```

上述编译脚本中的各种参数在build.html中都有具体介绍

这里需要注意的是**-with-boot-jdk**，如果没有安装jdk的话，需要指定jdk的位置。

编译成功后，可以在当前目录下执行**make imgaes**命令，如果机器好的话，大概几分钟就执行完成了



#### make images过程中出现的错误

执行过程中会错误很多的错误，都是源码中某一部分需要修改的。

##### 第一个错误

```
=== Output from failing command(s) repeated here ===
* For target hotspot_variant-server_libjvm_gtest_objs_logTestFixture.o:
In file included from /Users/jiaxiansheng/develop/jdk/jdk12-06222165c35f/test/hotspot/gtest/logging/logTestFixture.cpp:27:
/Users/jiaxiansheng/develop/jdk/jdk12-06222165c35f/test/hotspot/gtest/logging/logTestUtils.inline.hpp:34:70: error: suspicious concatenation of string literals in an array initialization; did you mean to separate the elements with a comma? [-Werror,-Wstring-concatenation]
  "=", "+", " ", "+=", "+=*", "*+", " +", "**", "++", ".", ",", ",," ",+",
                                                                     ^
                                                                    ,
/Users/jiaxiansheng/develop/jdk/jdk12-06222165c35f/test/hotspot/gtest/logging/logTestUtils.inline.hpp:34:65: note: place parentheses around the string literal to silence warning
  "=", "+", " ", "+=", "+=*", "*+", " +", "**", "++", ".", ",", ",," ",+",
                                                                ^
1 error generated.

* All command lines available in /Users/jiaxiansheng/develop/jdk/jdk12-06222165c35f/build/macosx-x86_64-server-fastdebug/make-support/failure-logs.
=== End of repeated output ===
```

**修改内容**

原内容

```
"=", "+", " ", "+=", "+=*", "*+", " +", "**", "++", ".", ",", ",," ",+",
```

修改后的内容

```
"=", "+", " ", "+=", "+=*", "*+", " +", "**", "++", ".", ",", ",,", ",+",
```



##### 第二个错误

```
=== Output from failing command(s) repeated here ===
* For target hotspot_variant-server_libjvm_objs_arguments.o:
/Users/jiaxiansheng/develop/jdk/jdk12-06222165c35f/src/hotspot/share/runtime/arguments.cpp:1452:35: error: result of comparison against a string literal is unspecified (use an explicit string comparison function instead) [-Werror,-Wstring-compare]
      if (old_java_vendor_url_bug != DEFAULT_VENDOR_URL_BUG) {
                                  ^  ~~~~~~~~~~~~~~~~~~~~~~
1 error generated.

* All command lines available in /Users/jiaxiansheng/develop/jdk/jdk12-06222165c35f/build/macosx-x86_64-server-fastdebug/make-support/failure-logs.
=== End of repeated output ===
```

**修改内容**

原内容

```
old_java_vendor_url_bug != DEFAULT_VENDOR_URL_BUG
```

修改后的内容

```
strcmp(old_java_vendor_url_bug, DEFAULT_VENDOR_URL_BUG) != 0
```



##### 第三个错误

```
=== Output from failing command(s) repeated here ===
* For target hotspot_variant-server_libjvm_objs_sharedRuntime.o:
/Users/jiaxiansheng/develop/jdk/jdk12-06222165c35f/src/hotspot/share/runtime/sharedRuntime.cpp:2873:85: error: expression does not compute the number of elements in this array; element type is 'double', not 'relocInfo' [-Werror,-Wsizeof-array-div]
      buffer.insts()->initialize_shared_locs((relocInfo*)locs_buf, sizeof(locs_buf) / sizeof(relocInfo));
                                                                          ~~~~~~~~  ^
/Users/jiaxiansheng/develop/jdk/jdk12-06222165c35f/src/hotspot/share/runtime/sharedRuntime.cpp:2872:14: note: array 'locs_buf' declared here
      double locs_buf[20];
             ^
/Users/jiaxiansheng/develop/jdk/jdk12-06222165c35f/src/hotspot/share/runtime/sharedRuntime.cpp:2873:85: note: place parentheses around the 'sizeof(relocInfo)' expression to silence this warning
      buffer.insts()->initialize_shared_locs((relocInfo*)locs_buf, sizeof(locs_buf) / sizeof(relocInfo));
                                                                                    ^
1 error generated.

* All command lines available in /Users/jiaxiansheng/develop/jdk/jdk12-06222165c35f/build/macosx-x86_64-server-fastdebug/make-support/failure-logs.
=== End of repeated output ===
```

**修改内容**

原内容

```
buffer.insts()->initialize_shared_locs((relocInfo*)locs_buf, sizeof(locs_buf) / sizeof(relocInfo))
```

修改后的内容

```
buffer.insts()->initialize_shared_locs((relocInfo*)locs_buf, (sizeof(locs_buf)) / (sizeof(relocInfo))
```

就是添加括号



##### 第四个错误

```
=== Output from failing command(s) repeated here ===
* For target hotspot_variant-server_libjvm_gtest_objs_test_symbolTable.o:
/Users/jiaxiansheng/develop/jdk/jdk12-06222165c35f/test/hotspot/gtest/classfile/test_symbolTable.cpp:62:6: error: explicitly assigning value of variable of type 'TempNewSymbol' to itself [-Werror,-Wself-assign-overloaded]
  s1 = s1; // self assignment
  ~~ ^ ~~
1 error generated.

* All command lines available in /Users/jiaxiansheng/develop/jdk/jdk12-06222165c35f/build/macosx-x86_64-server-fastdebug/make-support/failure-logs.
=== End of repeated output ===
```

**修改内容**

原内容

```
s1 = s1; // self assignment
```

修改后的内容

```
//s1 = s1; // self assignment
```

注释掉当前行



##### 第五个错误

```
=== Output from failing command(s) repeated here ===
* For target support_native_java.desktop_libjsound_PLATFORM_API_MacOSX_MidiUtils.o:
/Users/jiaxiansheng/develop/jdk/jdk12-06222165c35f/src/java.desktop/macosx/native/libjsound/PLATFORM_API_MacOSX_MidiUtils.c:263:31: error: cast to smaller integer type 'MIDIClientRef' (aka 'unsigned int') from 'void *' [-Werror,-Wvoid-pointer-to-int-cast]
static MIDIClientRef client = (MIDIClientRef) NULL;
                              ^~~~~~~~~~~~~~~~~~~~
/Users/jiaxiansheng/develop/jdk/jdk12-06222165c35f/src/java.desktop/macosx/native/libjsound/PLATFORM_API_MacOSX_MidiUtils.c:264:29: error: cast to smaller integer type 'MIDIPortRef' (aka 'unsigned int') from 'void *' [-Werror,-Wvoid-pointer-to-int-cast]
static MIDIPortRef inPort = (MIDIPortRef) NULL;
                            ^~~~~~~~~~~~~~~~~~
/Users/jiaxiansheng/develop/jdk/jdk12-06222165c35f/src/java.desktop/macosx/native/libjsound/PLATFORM_API_MacOSX_MidiUtils.c:265:30: error: cast to smaller integer type 'MIDIPortRef' (aka 'unsigned int') from 'void *' [-Werror,-Wvoid-pointer-to-int-cast]
static MIDIPortRef outPort = (MIDIPortRef) NULL;
                             ^~~~~~~~~~~~~~~~~~
/Users/jiaxiansheng/develop/jdk/jdk12-06222165c35f/src/java.desktop/macosx/native/libjsound/PLATFORM_API_MacOSX_MidiUtils.c:471:32: error: cast to smaller integer type 'MIDIEndpointRef' (aka 'unsigned int') from 'void *' [-Werror,-Wvoid-pointer-to-int-cast]
    MIDIEndpointRef endpoint = (MIDIEndpointRef) NULL;
                               ^~~~~~~~~~~~~~~~~~~~~~
   ... (rest of output omitted)

* All command lines available in /Users/jiaxiansheng/develop/jdk/jdk12-06222165c35f/build/macosx-x86_64-server-fastdebug/make-support/failure-logs.
=== End of repeated output ===
```

**修改内容**

原内容

```
(MIDIClientRef) NULL
```

修改后的内容

```
(unsigned long) NULL
```

将所有搜到**(MIDIClientRef) NULL**的地方都修改掉，大概是四个地方



#### 编译成功

```
Compiling 4 files for BUILD_JIGSAW_TOOLS
Stopping sjavac server
Finished building target 'default (exploded-image)' in configuration 'macosx-x86_64-normal-server-release'
```

可以在下面的目录下执行**./java -version**查看编译后的jdk版本

![image-20211016125208694](https://gitee.com/gluten/images/raw/master/images/202110212151448.png)

### IDEA使用编译后的JDK

1、idea添加一个jdk，具体路径就是编译后的jdk路径

![image-20211016125506985](https://gitee.com/gluten/images/raw/master/images/202110212151796.png)

2、添加后的jdk，sourcepath下是空的，需要自己手动添加一下，具体路径选择**src**

![image-20211016125726323](https://gitee.com/gluten/images/raw/master/images/202110212151320.png)

3、导入完成后，就可以创建一个项目了，选择刚刚添加的jdk，这时候创建测试类，就会发现源码是可以修改的了。

![image-20211016130022525](https://gitee.com/gluten/images/raw/master/images/202110212151092.png)

修改源码后，再次执行**make images**,这个编译时增量编译，所以不会耗太长时间，编译成功后在测试类中添加代码
![image-20211016130248488](https://gitee.com/gluten/images/raw/master/images/202110212152014.png)

运行后，会发现控制台会出现刚刚在源码中添加的内容