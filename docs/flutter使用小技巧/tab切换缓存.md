### tab切换缓存

#### tab页
```
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';


class SettingPage extends StatelessWidget {
  const SettingPage({super.key});

  @override
  Widget build(BuildContext context) {
    print("加载SettingPage");
    return Column(
      children: [
        Text("设置页面"),
      ],
    );
  }
}
```


#### 实现方式一
```
import 'package:flutter/material.dart';

import 'tabs/CategoryPage.dart';
import 'tabs/CustomTopBar.dart';
import 'tabs/HomePage.dart';
import 'tabs/SettingPage.dart';

class Tabs extends StatefulWidget {
  const Tabs({super.key});

  @override
  State<Tabs> createState() => _TabsState();
}

class _TabsState extends State<Tabs> {
  int _currentIndex = 0;
  List pages = [HomePage(), CategoryPage(), SettingPage(), CustomTopBarPage()];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
        appBar: AppBar(
          title: const Text("title"),
        ),
        body: this.pages[_currentIndex],
        bottomNavigationBar: BottomNavigationBar(
          type: BottomNavigationBarType.fixed,//多于三个的时候需要添加，作为修正使用
          currentIndex: this._currentIndex,
          onTap: (index) {
            setState(() {
              this._currentIndex = index;
            });
          },
          items: [
            BottomNavigationBarItem(icon: Icon(Icons.home), label: "首页"),
            BottomNavigationBarItem(icon: Icon(Icons.category), label: "分类"),
            BottomNavigationBarItem(icon: Icon(Icons.settings), label: "设置"),
            BottomNavigationBarItem(
                icon: Icon(Icons.add_business_outlined), label: "自定义导航")
          ],
        ));
  }
}
```
按照如上的实现方式，每一次点击tab页的时候都会重新加载页面，如果多次切换`SettingPage`页面，会发现每一次都会打印日志。

#### 实现方式二
我们可以使用一些第三方的包来完成页面的缓存
>>>   proste_indexed_stack: ^0.2.4
在`pubspec.yaml`中添加`proste_indexed_stack`包，
然后使用如下的实现方式：
```
import 'package:flutter/material.dart';
import 'package:proste_indexed_stack/proste_indexed_stack.dart';

import 'FoodieTab.dart';
import 'HomeTab.dart';
import 'SettingTab.dart';

class Tabs extends StatefulWidget {
  const Tabs({super.key});

  @override
  State<Tabs> createState() => _TabsState();
}

class _TabsState extends State<Tabs> {
  int _currentIndex = 0;
  List<TabModel> tabPages = [
    TabModel(tabWidget: HomeTab(), label: "首页", icon: Icon(Icons.home)),
    TabModel(
        tabWidget: FoodieTab(),
        label: "吃货",
        icon: Icon(Icons.food_bank_outlined)),
    TabModel(tabWidget: SettingTab(), label: "设置", icon: Icon(Icons.settings)),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // appBar: AppBar(title: Text('首页')),
      body: ProsteIndexedStack(
          index: _currentIndex,
          children: tabPages
              .map((tab) => IndexedStackChild(child: tab.tabWidget))
              .toList()),
      bottomNavigationBar: BottomNavigationBar(
          type: BottomNavigationBarType.fixed, //多于三个的时候需要添加，作为修正使用
          currentIndex: this._currentIndex,
          onTap: (index) {
            setState(() {
              this._currentIndex = index;
            });
          },
          items: tabPages
              .map((tab) =>
                  BottomNavigationBarItem(icon: tab.icon, label: tab.label))
              .toList()
          // [
          //   BottomNavigationBarItem(icon: Icon(Icons.home), label: "首页"),
          //   BottomNavigationBarItem(icon: Icon(Icons.settings), label: "设置"),
          // ],
          ),
    );
  }
}

/*
  tab
*/
class TabModel {
  Widget tabWidget;
  String label;
  Widget icon;
  TabModel({required this.tabWidget, required this.label, required this.icon});
}
```
使用`ProsteIndexedStack`，保证只有在第一次点击的时候才会加载，后期再次点击是不会在触发的。