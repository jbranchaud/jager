import sys
import subprocess
import time

#Replaces the / with a .
def replace(string, what, wit):
    for i in range(0, len(string)):
        if(string[i]==what):
            string = string[0:i]+wit+string[i+1:]
    return string


def slicePrefix(prefix, top):
    holder = replace(top, '.', "/")
    i = prefix.rfind(holder)
    return prefix[i+len(top):]
        
##Takes an array of complete class names -> eric.rizzi.Treemap
##Returns the path and the class seperated (eric.rizzi, Treemap)
def parseClassFile(arr):
    ret = []
    for a in arr:
        holder = a.strip().split(".")
        c = holder[-1]
        p = ""
        for i in range(0, len(holder)-1):
            p = p+holder[i]+"."
        if(len(p)<1):
            p=".."
        ret.append((p[0:-1], c))
    return ret

def createJPFFile(nc, c, path, package, dest):

    print("Open file")
    print(path+"/"+replace(package, ".", "/")+"/"+nc+"Driver.jpf\n\n")
    f2 = open(path+"/"+replace(package, ".", "/")+"/"+nc+"Driver.jpf", 'w')

    if(len(package)>1):
        f2.write("target = "+package+"."+c+"Driver")
    else:
        f2.write("target = "+c+"Driver")
    f2.write("\n\n")
    f2.write("classpath="+path)
    f2.write("\n\n")
    f2.write("symbolic.string_dp=automata")
    f2.write("\n\n")
    f2.write("symbolic.method="+package+"."+c+"Driver.testDriver(con)")
    f2.write("\n\n")
    f2.write("search.multiple_errors=true")
    f2.write("\n\n")
    f2.write("listener = gov.nasa.jpf.symbc.listeners.TargetedSE")
    f2.write("\n\n")
    f2.write("symbolic.package="+package+";Integer")
    f2.write("\n\n")
    f2.write("errorOfLine=-1")

    f2.close();

def getIndividualQueries(array):
    queries = []
    i =0
    primed = False

    while(i<len(array)):
        if("(" in array[i] and primed and "sym" in array[i]):
            holder = " " + array[i].lstrip(" ")
            holder = holder.rstrip("\n")
            queries.append(holder)
            primed = False
        else:
            if("YYConstraint" in array[i]):
                primed = True
            i = i + 1
    print("Length of Queries", len(queries))
    return cleanUpArray(queries)

def writeQueriesToFile(queries, dest, p, c):
    f3 = open(dest+"/queries.txt", 'a')
    f3.write("QUERY INFO Class: "+p+"."+c+" Tool: JPF")
    for line in queries:
        line = line.strip(" ")
        if(len(line)>1):
            f3.write(line)
            f3.write("\n\n\n")
    f3.close()

def cleanUpArray(array):
    ret = []
    for line in array:
        line = line.strip(" ")
        if(len(line)>1):
            ret.append(line)
    return ret

def createDriver(path, jpfLib, libraries, randoopLib, home, c, iterations, p):
    string = 'java -cp '+ path+":"+jpfLib+':.:'+libraries+':'+randoopLib + ' randoop.main.Main genDriver --classlist='+home+'/classfilewhole.txt --path='+path+'/'+replace(p, '.', '/') + ' --file_name='+c+'Driver --jpf_class='+c + ' --jpf_iterations='+str(iterations)+' --package_name='+p
    err = open(home+"/err.txt", 'a')
    print(string)
    err.write("\n\n\n\n\n\nOutput for creating Driver for Class "+c)
    a = subprocess.check_output(string.split())
    err.write(a)
    err.close()

    print(string)
    print("\n\n\n")

def compileDriver(jpfLib, path, libraries, p, c):
    string = "javac -g -cp "+jpfLib+":.:"+path+":"+libraries+" "+path+'/'+replace(p, '.', '/')+"/"+c+"Driver.java"
    print(string)
    print("\n\n\n")
    a = subprocess.check_output(string.split())

def runJPF(path, p, c, home, jpfLocation, inittimeout, secondarytimeout, finaltimeout):
    maxite = finaltimeout/secondarytimeout
    
    string = jpfLocation+" "+path+'/'+replace(p, '.', '/')+"/"+c+"Driver.jpf"
    print(string)
    
    f = open(home+"/out.txt", "w", 100)
    old = ""
    p=subprocess.Popen(string, shell=True, stdout=f)
    i = 0
    while p.poll() is None:
        p2 = subprocess.Popen("ls -al "+home+"/out.txt", shell=True, stdout=subprocess.PIPE)
        new, garbage = p2.communicate()
        if(old == new):
            break
        else:
            if(i==maxite):
                break
            print("Waiting")
            old = new
            time.sleep(inittimeout)
            if(inittimeout<secondarytimeout):
                inittimeout = secondarytimeout

            i = i + 1
    f.close()

def instrumentFiles(originalPath, instrumentedPath, coberturaPath, home):
    string = coberturaPath+"/cobertura-instrument.sh --destination "+instrumentedPath+" --datafile "+home+"/cobertura.ser "+originalPath
    print(string)
    print("\n\n\n")
    p=subprocess.Popen(string, shell=True)
    p.wait()

#Creates the file classname.Runner
def createJunitRunner(dest, package, className):
    f = open(dest+"/"+className+"Runner.java", "w")

    f.write("import org.junit.*;")
    f.write("\n")
    f.write("import "+package+".*;")
    f.write("\n\n")
    f.write("public class "+className+"Runner{")
    f.write("\n\n")
    f.write("   public static void main(String args[]) {")
    f.write("\n")
    f.write("       org.junit.runner.JUnitCore.main("+className+"Test.class.getName());")
    f.write("\n")
    f.write("   }")
    f.write("\n")
    f.write("}")
    
    f.close()

def compileAndRunTest(path, package, c, instrumentedPath, memory, dest, randoopLib, lib, coberturaLib):
    createJunitRunner(dest, package, c)
    
    string = "javac -J-Xmx"+memory+" -cp .:"+lib+":"+instrumentedPath+":"+dest+":"+randoopLib+" "+dest+"/"+c+"*.java"
    print(string)
    print("\n\n\n")
    p=subprocess.Popen(string, shell=True)
    p.wait()

    string = "java -Xmx"+memory+" -cp "+instrumentedPath+":"+path+":.:"+lib+":"+dest+":"+coberturaLib+"/cobertura.jar:"+randoopLib+" "+c+"Runner"
    print(string)
    print("\n\n\n")
    p=subprocess.Popen(string, shell=True)
    p.wait()
    

def updateReport(home, coberturaPath):
    string = coberturaPath+"/cobertura-report.sh --format xml --datafile "+home+"/cobertura.ser --destination "+home+"/report"
    print(string)
    print("\n\n\n")
    p=subprocess.Popen(string, shell=True)
    p.wait()
    
def writeErrorLog(p, c, home):
    f = open(home+"/out.txt", "r")
    f2 = open(home+"/errorLog.txt", "a")
    f2.write("\n\n\n\nErrors in "+p+"."+c+"\n") 
    for line in f:
        if("error #" in line[0:10]):
            f2.write(line)
    f.close()
    f2.close()
    

print("Hi Eric")


##Where to put classfile that is generated
home = "/Users/jessemiller/Desktop/Research/MattSebastian/Projects/HCC/CurrentTests/Mattsproject/randoopscripts"
##Main package (Only do the top level.  For example is package is eric.rizzi just do eric
package ="eric"
##Where the .class files are
path = "/Users/jessemiller/Documents/workspace/JPFTest/bin"
##Where to put the instrumented files
instrumentedPath = path+"/instrumented"
##Path to libraries
libraries = "../"
##Iterations
iterations = 1
#Desination of test cases
destination = "/Users/jessemiller/Desktop/Research/MattSebastian/Projects/HCC/CurrentTests/Mattsproject/outputs/tests"
##Timeout
inittimeout = 10
secondarytimeout = 100
finaltimeout = 90800 #3hours



#Don't Change

#jpfLib = "/work/esquared/erizzi2/JPF/jpf-core/build/*:/work/esquared/erizzi2/JPF/jpf-symbc/build/*:/work/esquared/erizzi2/JPF/jpf-symbc/build/jpf-symbc.jar"
#randoopLib = "../:/work/esquared/erizzi2/JPF/Randoop/Bam.jar:/work/esquared/erizzi2/JPF/Randoop/lib/*"
#jpfLocation = "/work/esquared/erizzi2/JPF/jpf-core/bin/jpf"
#key = "work"
#coberturaLib =
#memory = "120g"

jpfLib = "/Users/jessemiller/Desktop/JPF/jpf-core/build/*:/Users/jessemiller/Desktop/JPF/jpf-symbc/build/*:/Users/jessemiller/Desktop/JPF/jpf-symbc/build/jpf-symbc.jar"
randoopLib = "../:/Users/jessemiller/Documents/workspace/Randoop/bin:/Users/jessemiller/Desktop/randoop/lib/*"
jpfLocation = "/Users/jessemiller/Desktop/JPF/jpf-core/bin/jpf"
key = "Users"
coberturaLib = "/Users/jessemiller/Desktop/Research/MattSebastian/Projects/HCC/CurrentTests/cobertura-1.9.4.1"
memory = "256m"


#Begin Actual Program
if(package!=""):
    package = package+"."

try:
    string = "rm " +home+"/errorLog.txt"
    subprocess.check_output(string.split())
    
except subprocess.CalledProcessError:
    print("errorLog.txt didn't exist yet")

numQueries = 0
classFile = []

f = open(home+"/classfile.txt", "r")
for line in f:
    classFile.append(line)
f.close()

classes = parseClassFile(classFile)

#For each class, put the driver file into the same spot
for (p, c) in classes:
    queries = []

    try:
        string = "rm "+home+"/err.txt"
        subprocess.check_output(string.split())

        string = "rm "+home+"/out.txt"
        subprocess.check_output(string.split())

    except subprocess.CalledProcessError as e:
        g = 4


    f = open(home+"/completed.txt", "a")
    f.write("Starting to test class "+p+"."+c+" \n")
    f.close()
        


    if("$" not in c):


        nc = c.replace("$", "\$")

        print("\n\n\n\n ",nc,"\n",c," \n\n\n\n")
    
        print("Create Driver?")
        try:
            #Create Driver
            print("Create Driver")
            createDriver(path, jpfLib, libraries, randoopLib, home, nc, iterations, p)


            ##Try to compile Driver
            print("Compile Driver")
            compileDriver(jpfLib, path, libraries, p, nc)


            #Create JPF File
            print("Create JPF File")
            createJPFFile(nc, c, path, p, destination)

            #Run JPF
            print("Run JPF")
            runJPF(path, p, nc, home, jpfLocation, inittimeout, secondarytimeout, finaltimeout)


            ##Write error Log
            writeErrorLog(p, c, home)


        except subprocess.CalledProcessError as e:
            print("XXXX Problems with", c)
            print(e.output)
            print("oops")

print("Bye ERic")
