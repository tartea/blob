git回滚代码就是将原本指向head的指针修改为指向其他地方

![image-20220415181000379](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202204151810473.png)

### 修改方法

#### 方法一

##### 原理

git reset的作用是修改HEAD的位置，即将HEAD指向的位置改变为之前存在的某个版本

![image-20220415181050441](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202204151810465.png)

**适用场景：** 如果想恢复到之前某个提交的版本，且那个版本之后提交的版本我们都不要了，就可以用这种方法。

##### 具体操作方法

![image-20220415181252711](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202204151812744.png)

```shell
#获取提交的日志
git log

#回退版本
git reset --hard 具体的版本号

#强制推送，此时如果用“git push”会报错，因为我们本地库HEAD指向的版本比远程库的要旧
git push -f
```

### 方法二

#### 原理

 git revert是用于“反做”某一个版本，以达到撤销该版本的修改的目的。比如，我们commit了三个版本（版本一、版本二、 版本三），突然发现版本二不行（如：有bug），想要撤销版本二，但又不想影响撤销版本三的提交，就可以用 git revert 命令来反做版本二，生成新的版本四，这个版本四里会保留版本三的东西，但撤销了版本二的东西。如下图所示：

![image-20220415181457919](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202204151814949.png)

**适用场景：** 如果我们想撤销之前的某一版本，但是又想保留该目标版本后面的版本，记录下这整个版本变动流程，就可以用这种方法。

```shell
#获取版本号
git log

#删除不需要的版本
git revert -n 版本号

#这里可能会出现冲突，那么需要手动修改冲突的文件。
git commit -m "注释"

#推送
git push

```

### 使用Idea回滚代码

![image-20220415182009427](https://images-1258301517.cos.ap-nanjing.myqcloud.com/images/202204151820461.png)

从上图可以看到有两个按钮，分别是`Reset Current Branch to Here`和`Revert Commit`，它们分别对应方法一和方法二。

使用`Reset Current Branch to Here`的时候对应方法一，选择某一个历史，然后触发动作，这时候不用使用idea中的push按钮，改使用命令 `git push -f`来强制推送，不然不能回滚成功。

使用`Revert Commit`会生成一条commit记录，这时候使用idea的push按钮就可以了。