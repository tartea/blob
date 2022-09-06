### 构建form表单

如果使用常规的`TextField`虽然是可以显示输入框，但是要实现校验功能的话，可能就比较麻烦，因此flutter又增加了`TextFormField`来完善该功能，具体如下：
```flutter
import 'package:flutter/material.dart';
import 'package:love_diary/components/toast_util.dart';
import 'package:love_diary/constants.dart';
import 'package:love_diary/services/login/login_service.dart';

import 'already_have_an_account_acheck.dart';

/*
登陆页面
 */
class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final GlobalKey _formKey = GlobalKey<FormState>();
   String? _phone;
   String? _password;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      resizeToAvoidBottomInset: false,
      body: Container(
          width: double.infinity,
          height: MediaQuery.of(context).size.height,
          child: SafeArea(
              child: Form(
                  key: _formKey, // 设置globalKey，用于后面获取FormStat
                  autovalidateMode: AutovalidateMode.onUserInteraction,
                  child: ListView(
                      padding: const EdgeInsets.symmetric(horizontal: 20),
                      children: [
                        SizedBox(height: 300),
                        buildPhoneTextField(), // 输入手机号
                        SizedBox(height: 20),
                        buildPasswordPhoneTextField(),
                        SizedBox(height: 20),
                        buildLoginButton(context), // 登录按钮
                        SizedBox(height: 20),
                        AlreadyHaveAnAccountCheck(
                          press: () {
                            Navigator.pushReplacementNamed(context, "signUp");
                          },
                        ),
                      ])))),
    );
  }

//构建电话号码
  Widget buildPhoneTextField() {
    return TextFormField(
      keyboardType: TextInputType.phone,
      textInputAction: TextInputAction.next,
      decoration: InputDecoration(
          labelText: '手机号码',
          prefixIcon: Padding(
            padding: EdgeInsets.all(defaultPadding),
            child: Icon(Icons.phone),
          ),
          border:
              OutlineInputBorder(borderRadius: BorderRadius.circular(32.0))),
      validator: (v) {
        var phoneReg = RegExp(
            r'^((13[0-9])|(14[0-9])|(15[0-9])|(16[0-9])|(17[0-9])|(18[0-9])|(19[0-9]))\d{8}$');
        if (!phoneReg.hasMatch(v!)) {
          return '请输入正确的手机号码';
        }
      },
      onSaved: (v) => _phone = v!,
    );
  }

//构建密码
  Widget buildPasswordPhoneTextField() {
    return TextFormField(
      obscureText: true,
      textInputAction: TextInputAction.done,
      decoration: InputDecoration(
          labelText: '密码',
          prefixIcon: Padding(
            padding: EdgeInsets.all(defaultPadding),
            child: Icon(Icons.lock),
          ),
          border:
              OutlineInputBorder(borderRadius: BorderRadius.circular(32.0))),
      validator: (v) {
        var passwordReg = RegExp(r"^[ZA-ZZa-z0-9_]{6,20}$");
        if (!passwordReg.hasMatch(v!)) {
          return '请输入正确的密码';
        }
      },
      onSaved: (v) => _password = v!,
    );
  }

  Widget buildLoginButton(BuildContext context) {
    return Align(
      child: SizedBox(
        height: 45,
        width: 270,
        child: ElevatedButton(
          style: ButtonStyle(
              // 设置圆角
              shape: MaterialStateProperty.all(const StadiumBorder(
                  side: BorderSide(style: BorderStyle.none)))),
          child:
              Text('登陆', style: Theme.of(context).primaryTextTheme.headline5),
          onPressed: () async {
            // 表单校验通过才会继续执行
            if ((_formKey.currentState as FormState).validate()) {
                //用来保存数据
              (_formKey.currentState as FormState).save();
                print("电话号码： $this._phone")
            }
          },
        ),
      ),
    );
  }
}

```