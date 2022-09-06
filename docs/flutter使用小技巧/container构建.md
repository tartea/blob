### container构建
通过对`decoration`进行修饰，可以形成特定样式的卡片
```
Container(
      height: 100,
      width: double.infinity,
      decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(10),
          //背景装饰
          gradient: RadialGradient(
            //背景径向渐变
            colors: [
              Color.fromARGB(255, 255, 255, 255),
              Color.fromARGB(255, 255, 255, 255)
            ],
            radius: 0.8,
          ),
          boxShadow: [
            //卡片阴影
            BoxShadow(
              color: Color.fromARGB(137, 119, 118, 118),
              offset: Offset(1.0, 1.0),
              blurRadius: 4.0,
            )
          ]),
      child: Text("123"),
    )
```
