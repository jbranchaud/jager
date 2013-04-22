import sys
import FaultLocalization
from z3 import *


def getIndividualPaths(f):
    f = open(f,"r")    
    arr = []
    trace = []
    for line in f:
        line = line.strip()
        if(len(line)>0):
            if(line[0]=="*"):
		if(len(trace)>0):
               	    arr.append(trace)
                    trace = []
            else:
                trace.append(line)
    if(len(trace)>0):
        arr.append(trace)
    return arr

def getVariables(string, oldMap):
    #Tokenize
    string = string.replace("(","")
    string = string.replace(")","")
    string = string.strip("")
    
    tokens = string.split()
    for token in tokens:
        if(len(token)>0 and ord(token[0])>96 and ord(token[0])<123):
            if(token not in oldMap):
                oldMap[token] = Int(token)
    return oldMap

def getVariablesPre(string, oldMap):
    #Tokenize
    string = string.replace("("," ")
    string = string.replace(")"," ")
    string = string.strip("")
    
    tokens = string.split()
    for token in tokens:
        if(len(token)>0 and ord(token[0])>96 and ord(token[0])<123):
            newtoken = token+str(1)
            if(newtoken not in oldMap):
                oldMap[token] = Int(newtoken)
            else:
                oldMap[token] = oldMap[newtoken]
    return oldMap

#returns integer
def parseInt(v, token):
    clean = token[:-1]  #get rid of the f
    if(clean==v):
        return 0
    elif(clean in v):
        ret = v[len(clean):]
        return int(ret)
    else:
        return -1

def getVariablesPost(string, oldMap):
    #Tokenize
    string = string.replace("("," ")
    string = string.replace(")"," ")
    string = string.strip("")
    
    tokens = string.split()
    for token in tokens:
        if(len(token)>0 and ord(token[0])>96 and ord(token[0])<123):
            last = -1
            for v in variables:
                num = parseInt(v, token)
                if(last < num):
                    last = num
            if(last==-1):
                oldMap[token] = Int(token)
            elif(last==0):
                last = token[0:-1]
                oldMap[token] = oldMap[last]
            else:
                last = token[0:-1]+str(last)
                oldMap[token] = oldMap[last]
    return oldMap

def getConstraints(arr):
    constraints = []
    variables = {}
    for a in arr:
        variables = getVariables(a, variables)
        constraints.append(eval(a, {},variables))
    return constraints, variables


def solve(constraints, variables, preconditions, postconditions):
    s = Solver()
    variables["Or"]=Or
    variables["And"]=And
    variables["Not"]=Not
    
    for pre in preconditions:
        variables = getVariablesPre(pre, variables)
        #for thing in variables:
        #    print(thing+" -> "+str(id(variables[thing])))
        s.add(eval(pre, {}, variables))

    for c in constraints:
        s.add(c)

    for post in postconditions:
        variables = getVariablesPost(post, variables)
        #for thing in variables:
        #    print(thing+" -> "+str(id(variables[thing])))
        s.add(eval("Not("+post+")", {}, variables))
        
    return s

def getParts(line):
    try:
        s = line.split(",")
        return s[0], s[1]
    except IndexError, e:
        print("Error: Line number not associated with statement!")

def parse(arr):
    ret = []
    for a in arr:
        statement, lineNum = getParts(a)
        ret.append(statement)
    return ret

        
        

def prettyPrint(outputfile, arr, solution, i):
    f = open(outputfile, "a")
    f.write("  - id: trace"+str(i))
    f.write("\n")

    if(str(solution)=="sat"):
        gb = "bad"
    else:
        gb = "good"
    f.write("    status: "+gb)
    f.write("\n")

    f.write("    statements: ")
    f.write("\n")

    for line in arr:
        statement, lineNum = getParts(line)

        f.write('      - statement: "'+statement+'"')
        f.write("\n")

        f.write("        line: "+lineNum)
        f.write("\n")

    f.close()

def printFooter(outputfile):
    f = open(outputfile, "a")
    f.write("...")
    f.close()


def printHeader(outputfile, preconditions, postconditions, programID, otherInfo):
    f = open(outputfile, "w")

    f.write("---")
    f.write("\n")
    
    f.write("programid: "+programID)
    f.write("\n")
    for info in otherInfo:
        f.write("#"+info)
        f.write("\n")
        
    f.write("preconditions: ")
    f.write("\n")
    for condition in preconditions:
        f.write('  - "'+condition+'"')
        f.write("\n")

    f.write("postconditions: ")
    f.write("\n")
    for condition in postconditions:
        f.write('  - "'+condition+'"')
        f.write("\n")

    f.write("traces: ")
    f.write("\n")
        
    f.close()


traceFile = "/Users/jessemiller/Documents/UNL/2012-13/2ndSemester/ProgramSynthesis/TermProject/jager/output/traces.txt"
outputfile = "/Users/jessemiller/Documents/UNL/2012-13/2ndSemester/ProgramSynthesis/TermProject/jager/output/gbtraces.txt"

preconditions = []
##Just for now, label all variables as xf and yf to designate final
postconditions = ["retf > 1"]
programId = "None"
otherInfo = []

printHeader(outputfile, preconditions, postconditions, programId, otherInfo)
arr = getIndividualPaths(traceFile)
i = 0
while(i<len(arr)):
    print("Evaluating trace "+str(i))
    #Split the pieces up so don't have the line number
    trace = parse(arr[i])

    #Evaluate each line in the constraint so it can be used by Z3
    constraints, variables = getConstraints(trace)

    #Call the solver
    s = solve(constraints, variables, preconditions, [])

    #For the Z3 solver is more powerful than jpf so make sure feasible path
    #Just as a feasibility note, we are using the SAT solver five times when only need to twice
        #1) With JPF when generating initial traces
        #2) With Z3 to make sure traces will work with preconditions (Also because z3 is more powerful than Choco)
            #This wouldn't be needed if could insert pre and postconditions into java file
        #3) To see if the trace, given that it works with preconditions, violates the postconditions
            #This wouldn't be needed for the same reasons above, then could capture it with JPF failing state in listener
        #4) To generate all the traces after the bad line
        #5) To make sure the generated traces after the bad line are valid since Z3 better than JPF
    print(s.check())
    if(str(s.check())=="sat"):
        
        s = solve(constraints, variables, preconditions, postconditions)

        if(str(s.check())=="sat"):
            print("Bad trace")
            print(s)
            print(str(s.model()))
        else:
            print("good trace")
        prettyPrint(outputfile, arr[i], str(s.check()), i)

    i = i + 1

printFooter(outputfile)
print("Done parsing traces")

listBugs = FaultLocalization.rank_statements(outputfile)
print(listBugs)

