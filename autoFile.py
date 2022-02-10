import os

filePath = os.getcwd()

# 读取第一级的文件和目录
def readFile(fo):
  rootdir = filePath + '/docs'
  list = getAndSortedFile(rootdir) #列出文件夹下所有的目录与文件
  print(list)
  for i in range(0,len(list)):
      path = os.path.join(rootdir,list[i])
      if os.path.isdir(path):
        fo.write("## " +os.path.basename(list[i]) +"\n") 
        fo.write("------\n") 
        readDeepFile("###",fo,path)
        fo.write("\n") 
      elif os.path.isfile(path):
        checkFile(path,fo)

# 递归读取二级甚至更深的目录和文件
def readDeepFile(prefix,fo,pathDir):
    list = getAndSortedFile(pathDir) #列出文件夹下所有的目录与文件
    for i in range(0,len(list)):
      path = os.path.join(pathDir,list[i])
      if os.path.isdir(path):
        fo.write(prefix + " " +os.path.basename(list[i]) +"\n") 
        readDeepFile("####",fo,path)
        fo.write("\n") 
      elif os.path.isfile(path):
        checkFile(path,fo)

# 判断文件是否是markdown文件
def checkFile(file,fo):
    root, extension = os.path.splitext(file)
    if(extension == ".md"):
      fileName = os.path.basename(file);
      if(not fileName.startswith("__")):
          fo.write("- [" +fileName.replace(".md",'')+"](" +file.replace(filePath,'')+")\n") 

def getAndSortedFile(pathDir):
    files = os.listdir(pathDir) #列出文件夹下所有的目录与文件
    return sorted(files,  key=lambda x: os.path.getctime(os.path.join(pathDir, x)))

def writeFile():
  fo = open(filePath + "/README.md", "w")
  readFile(fo) 
  # 关闭打开的文件
  fo.close()      

writeFile()