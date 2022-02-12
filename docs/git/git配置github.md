### 设置SSH

```shell
ssh-keygen -t rsa -b 4096 -C "git@qq.com"
```

获取生成的key

```shell
cd ~/.ssh
cat id_rsa.pub
```

可以看到文件的具体内容，然后将该内容复制到github的SSH当中

![image-20220210165442028](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202202101654082.png)

使用`ssh -T git@github.com`验证是否配置成功

![image-20220210165810843](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202202101658880.png)

出现以上内容，说明配置已经成功了

### 配置仓库

> 这里默认以为github上已经存在一个仓库。

在仓库下选择ssh地址

![image-20220210165955324](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202202101659367.png)

**注意不要使用https的链接，github现在不支持用户名密码的方式了，前面配置的ssh在这里就起作用了**

下载仓库

```shell
git clone git@github.com:tartea/blob.git
```

下载完成后，可以简单的配置一下当前仓库的一些信息，如用户名

```shell
git config user.name "jiawenhao"
git config user.email 1121@qq.com
```

上面的配置只对当前仓库有效，如果想配置全局的，那么需要添加参数`--global`

### 提交文件

在配置完仓库后，就可以将一些文件提交到github上面了，具体有用到的命令如下：

```shell
#添加新的文件到暂存区
git add index.html
#添加当前目录下的所有文件到暂存区
git add .
#查看仓库当前的状态，显示有变更的文件。
git status
#显示暂存区和上一次提交到差异
git diff --cached [file]
#提交文件到本地仓库
git commit -m "注释"
#提交指定文件
git commit [file] -m "注释"
#提交文件时忽略git add
git commit -a
# 回退所有内容到上一个版本  
git reset HEAD^       
# 回退 hello.php 文件的版本到上一个版本 
git reset HEAD^ hello.php   
# 回退到指定版本
git  reset  052e
#查看历史提交记录
git log 
#以列表形式查看指定文件的历史修改记录
git blame <file> 
#下载远程代码，并合并本地的版本
git pull
#提交本地的代码 本地版本与远程版本有差异，但又要强制推送可以使用 --force 参数
git push

```

### git将本地仓库提交到github

```shell
git init
git add README.md
git commit -m "first commit"
git branch -M main
```

在github上创建一个仓库，然后使用下面的命令将本地的git关联到github

```shell
git remote add origin git@github.com:tartea/study-parent.git
git push -u origin main
```

