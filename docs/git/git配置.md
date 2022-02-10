通常我们通过下面的命令来设置全局的配置

```git
git config --global user.name "jiawenhao"
git config --global user.email 1121@qq.com
```

但是这种配置会导致我们在某一个项目提交的时候，改变条件的用户名称

如：

我们平时在A项目中提交的时候，使用的用户名名称是**xiaoming**，但是设置了全局的username----zhansan，那么在A项目再次提交一份文件的时候，会发现用户名称变成了**zhansan**

所以在日常的开发中如果需要修改用户名称的时候，可以在指定的git目录下执行命令，但是不使用**--global**参数

```
git config user.name "jiawenhao"
```

这样就可以只针对当前的项目了。

可以通过使用`git config -e`或者查看**.git**目录下的config文件，查看当前git环境的配置

```
[core]
        repositoryformatversion = 0
        filemode = true
        bare = false
        logallrefupdates = true
        ignorecase = true
        precomposeunicode = true
[remote "origin"]
        url = 
        fetch = +refs/heads/*:refs/remotes/origin/*
[branch "dev"]
        remote = origin
        merge = refs/heads/dev
[user]
        name = jiawenhao

```

可以通过使用`git config --global -e`查看全局的配置

```
[user]
        name = jiaxiansheng
        email = 1262466460@qq.com

#[http]
#        proxy = socks5://127.0.0.1:7890
#[https]
#        proxy = socks5://127.0.0.1:7890
```

