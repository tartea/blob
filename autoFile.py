import os

filePath = '/Users/jiaxiansheng/Github/blob'


def readFile(fo):
  rootdir = '/Users/jiaxiansheng/Github/blob/docs'
  list = os.listdir(rootdir) #列出文件夹下所有的目录与文件
  for i in range(0,len(list)):
      path = os.path.join(rootdir,list[i])
      if os.path.isdir(path):
        fo.write("## " +os.path.basename(list[i]) +"\n") 
        fo.write("------\n") 
        readDeepFile("###",fo,path)
        fo.write("\n") 
      elif os.path.isfile(path):
        checkFile(path,fo)


def readDeepFile(prefix,fo,pathDir):
    list = os.listdir(pathDir) #列出文件夹下所有的目录与文件
    for i in range(0,len(list)):
      path = os.path.join(pathDir,list[i])
      if os.path.isdir(path):
        fo.write(prefix + " " +os.path.basename(list[i]) +"\n") 
        readDeepFile("####",fo,path)
        fo.write("\n") 
      elif os.path.isfile(path):
        checkFile(path,fo)

def checkFile(file,fo):
    root, extension = os.path.splitext(file)
    if(extension == ".md"):
      fileName = os.path.basename(file);
      if(not fileName.startswith("__")):
          fo.write("- [" +fileName.replace(".md",'')+"](" +file.replace(filePath,'')+")\n") 


def writeFile():
  fo = open("/Users/jiaxiansheng/Github/blob/README.md", "w")
  readFile(fo) 
  # 关闭打开的文件
  fo.close()      

writeFile()