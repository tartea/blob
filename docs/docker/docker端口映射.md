如果一个docker镜像已经存在，那么如果想再添加映射端口，一般都会删除该镜像，然后重新配置。但是在实际的使用当中，很多时候都会想着如果能动态添加一个端口，那该多好。

### 动态修改

```shell
#找到容器的PID
docker ps -a
#找到容器的位置
docker inspect PID |grep ResolvConfPath
#进入容器内部，修改对应的配置文件

vi config.v2.json
#在ExposedPorts下添加想要添加的端口
vi hostconfig.json
"61613/tcp":{}

#在PortBindings下添加端口
"61613/tcp":[{"HostIp":"","HostPort":"61613"}]
```

由于docker不支持mac，所以在mac下使用的是虚拟机，docker镜像的位置直接切换到指定目录是找不到的，需要先通过指定命令登陆到容器，然后才可以找到镜像的位置

```
screen ~/Library/Containers/com.docker.docker/Data/vms/0/tty
cd path
```

有的mac版本可能在执行上述命令的时候没有反应或者找不到文件目录，这时候需要使用另外一种方式登陆

```
docker run -it --privileged --pid=host justincormack/nsenter1
cd path
```