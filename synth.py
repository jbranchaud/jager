import sys
from z3 import *
import copy

#Assumptions
#1) All preconditions come of the form x, y, and z
#2) All postconditions come of the form xf, yf, and zf
#3) All variables are simple strings, no x1's since in ssa form that could be confused for x11 eventuall
#4) All input traces are of the form yf2 == xf1 + 1, 13 or statement, linenum more generally
#5) All bottom traces represent variables as xf1, yf1, ...
#6) All top traces represents variables as x1, x2, y1, ...

#This object keeps track of the first and last instance of a variable
#used within a single trace.  for example start=x1 and end = xpreHole
class Variable(object):
    #start and end are strings that can be used to access the first and last instance
    #of a variable used in a trace
    def __init__(self, start):
        self.start = start
        self.end = start
        
    def setStart(self, start):
        self.start = start
        
    def setEnd(self, end):
        self.end = end
        
    def getEnd(self):
        return self.end
    
    def getStart(self):
        return self.start
    
    def toString(self):
        return "Start: "+self.start+" End: "+self.end
    
    ##Takes a pattern and sees if should be new start or new end
    def process(self, pattern, prospect):
        if(prospect != self.start and self.lessThan(prospect, self.start, pattern)):
            self.start = prospect
        if(prospect != self.end and self.lessThan(self.end, prospect, pattern)):
            self.end = prospect

    ##Returns whether the p1 is less than p2 given some pattern then
    ##have in common.  Usually (always) this pattern will be the variable
    ##name
    def lessThan(self, p1, p2, pattern):
        if(p1==pattern):
            return True
        if(p2==pattern):
            return False
        c1 = p1[len(pattern):]
        c2 = p2[len(pattern):]
        if(c2=="f"):
            return True
        if(c1=="f"):
            return False
        return int(c1) < int(c2)

#trace is an array of arrays of simple statements [[("variable", "x"),("op", "+"),("variable","y")],[...]]
#variablesMap is a map from the basename of a variable in the program to a Variable object
#stitch is an array containing all of the new variables that come from raising a precondition's
#constraints to preHole.  For example it will contain statements like xf3 == xpreHole except as seen
##in the trace from above.
class Trace(object):
    def __init__(self, trace, variablesMap):
        self.trace = trace
        self.variablesMap = variablesMap
        self.stitch = []

    #Returns the trace, and the raised preconditions (if any) with the tracenum appended
    #This is important to differentiate between the x's of different variables
    def getAndTrace(self, traceNum):
        if(len(self.trace)>0):
            string = ""
            holder = ""
            for a in self.trace[0]:
                if(a[0]=="variable"):
                    holder = holder + " " + a[1] + traceNum
                else:
                    holder = holder + " " + a[1]
            string = holder.strip()

            i = 1
            while(i<len(self.trace)):
                holder = ""
                for a in self.trace[i]:
                    if(a[0]=="variable"):
                        holder = holder + " " + a[1] + traceNum
                    else:
                        holder = holder + " " + a[1]
                string = "And( "+holder.strip()+", "+string+")"

                i = i + 1

            i = 0
            while(i<len(self.stitch)):
                holder = ""
                for a in self.stitch[i]:
                    if(a[0]=="variable"):
                        holder = holder + " " + a[1] + traceNum
                    else:
                        holder = holder + " " + a[1]
                string = "And( "+holder.strip()+", "+string+")"

                i = i + 1
                
            return string
        else:
            return ""


    def toString(self):
        string = "Trace:\n"
        for con in self.trace:
            string = string+" "+str(con)+","
        string = string.strip(", ")
        string = string+"\n"
        
        for v in self.variablesMap:
            string = string + " " + v + " -> " + self.variablesMap[v].toString()
        string = string+"\n"

        return string

    ##This adds the postconditions of the entire program to the bottom of a trace.
    ##It does three things.  First, it makes every last use of a variable in ssa form
    ##equal the variable in postcondition form.  xf5 == xf.  Second, it updates the
    ##variable map so the "end" of the variable is the postcondition.  Finally, it
    ##adds the post conditions to the end of the trace.
    def weavePost(self, other):
        otrace = other.getTrace()
        ovariablesMap = other.getVariablesMap()
        
        #For all of the variables in the trace, create a link with the postcondition variables
        for v in ovariablesMap:
            found = False
            for myv in self.variablesMap:
                if(myv in v):
                    newCon = []
                    newCon.append(("variable",self.variablesMap[myv].getEnd()))
                    newCon.append(("op"," == "))
                    newCon.append(("variable",ovariablesMap[v].getStart()))
                    self.variablesMap[myv].setEnd(ovariablesMap[v].getStart())
                    self.trace.append(newCon)
                    found = True
            if(not found):
                self.variablesMap[v]=ovariablesMap[v]

        for t in otrace:
            self.trace.append(t)

    ##Basically the same as weavePost
    def weavePre(self, other):
        otrace = other.getTrace()
        ovariablesMap = other.getVariablesMap()

        ##For all of the variables in the trace, create a link with the precondition variables
        for v in ovariablesMap:
            found = False
            for myv in self.variablesMap:
                if(v in myv):
                    #Link the variables of the precondition with the variables in the actual trace
                    newCon = []
                    newCon.append(("variable",ovariablesMap[v].getEnd()))
                    newCon.append(("op"," == "))
                    newCon.append(("variable",self.variablesMap[myv].getStart()))
                    self.variablesMap[myv].setEnd(self.variablesMap[myv].getEnd())
                    self.variablesMap[myv].setStart(ovariablesMap[v].getStart())
                    self.trace.insert(0, newCon)
                    found = True
            if(not found):
                self.variablesMap[v]=ovariablesMap[v]
                

        ##Add all of the constraints that came with the precondition
        for t in otrace:
            self.trace.insert(0, t)

    def getVariablesMap(self):
        return self.variablesMap

    def getTrace(self):
        return self.trace

    #Although this method could have been integrated into stitch, I had them seperate
    #when I though that you had to keep each instance of an int (Int("x")) referenced
    ##by the trace that used it.  Luckily this isn't the case and the solver goes on
    ##purely syntatic solving.  Anyways, this method basically just takes the last
    ##instance of every variable in ssa form and creates a condition so that it equals
    ##the preHole of the variable (xf3 == xpreHole).  Stitch then finishes the job by
    ##doing xpreHole -> xf1 in all cases but the rhs variable.
    def raisePreConditions(self, variblesUsed):
        for v in self.variablesMap:
            newCon = []
            newCon.append(("variable",self.variablesMap[v].getEnd()))
            newCon.append(("op"," == "))
            newCon.append(("variable",v+"preHole"))
            string = v+"preHole"
            self.variablesMap[v].setEnd(string)
            variablesUsed.append(string)
            self.stitch.append(newCon)
            self.andTrace = ""

    ##All stitch really does is move all the instances of
    ##xpreHole to xf1
    ##Although this clearly isn't good practice, it returns the
    ##names of the variables before the hole (available) with the
    ##trace name attached.  I would have prefered to do that under
    ##the getAndTrace method so the trace was calculated all in one
    ##spot
    def stitchIt(self, rhs, variablesUsed, sig):

        available = {}  ##The variables that surround the hole

        preHoleVariables = self.variablesMap

        for v in preHoleVariables:
            if(rhs != v):
                preHoleVariables[v].setEnd(v+"f"+str(1))
                for a in self.stitch:
                    if(v in a[0][1]):
                        string = v+"f"+str(1)
                        a[2] = ("variable", string)
                        if(string not in variablesUsed):
                            variablesUsed.append(string)
                            available[v] = string
            else:
                available[v] = rhs+"preHole"+sig
                available["rhs"] = v+"f"+str(1)+sig

        return available

##This method takes a trace from a file and breaks it up into distinct traces.
##Each new trace should start with *****.  It returns an array of the from
##["yf2 == xf1 + 1, 13", "xf1 < 10, 14", ...]
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

##This function splits the trace statement given in the file into two seperate
##parts.  The first is the statement, the second is the line number
def getParts(line):
    try:
        s = line.split(",")
        return s[0], s[1]
    except IndexError, e:
        print("Error: Line number not associated with statement!")

##Gets all of the statements up to the errorLine number.  Note: Actual preconditions still need to be added
def getUpToBug(errorLine, arr):
    ret = []
    for trace in arr:
        holder = []
        for line in trace:
            statement, lineNum = getParts(line)
            lineNum = lineNum.strip()
            if(lineNum == errorLine):
                ret.append(holder)
                break
            else:
                holder.append(statement)
    return ret

##Silly to have this functionality, but returns a trace as an array without
##the line number.
def loseLineNumbers(arr):
    ret = []
    for a in arr:
        statement, lineNum = getParts(a)
        ret.append(statement)
    return ret

##This function does two things.
##1) It assembles the map of all variables used within the program
##2) It evaluates each of the simple statements in the trace, and makes a trace object out of it
def getConstraints(arr, variablesUsed):
    constraints = []
    ##Represents the variables used in a particular trace.  It is a map from a string (ie. x) to a Variable object
    variablesLocalMap ={}

    constraints = []
    for a in arr:
        a, variablesUsedMap, variablesUsed = getVariables(a, variablesLocalMap, variablesUsed)
        constraints.append(a)
    t = Trace(constraints, variablesLocalMap)
    return t, variablesUsed

##Takes a token of the form x18 and returns x
def parseToken(token):
    i = 0
    while(i<len(token) and not(ord(token[i])>=48 and ord(token[i])<= 57)):
        i = i + 1
    return token[:i]


def getVariables(string, variablesLocalMap, variablesUsed):
    pieces = []
    
    #Tokenize
    string = string.replace("("," ( ")
    string = string.replace(")"," ) ")
    string = string.replace(","," , ")
    string = string.strip("")
    
    tokens = string.split()
    for token in tokens:
        if(len(token)>0 and ord(token[0])>96 and ord(token[0])<123):
            pieces.append(("variable",token))

            if(token not in variablesUsed):
                variablesUsed.append(token)
                
            basicPattern = parseToken(token)

            if(basicPattern not in variablesLocalMap):
                variablesLocalMap[basicPattern] = Variable(token)
            else:
                variablesLocalMap[basicPattern].process(basicPattern, token)
        else:
            pieces.append(("op",token))

    return pieces, variablesLocalMap, variablesUsed

##This function creates a map for all of the variables used in a particular
##trace to one that includes the tracesignature.  This is for eval()
def createAllUsedVariablesMap(variablesUsedMap, variables, traceSig):
    for v in variables:
        varName = v+traceSig
        variablesUsedMap[varName] = Int(varName)
    return variablesUsedMap

##This combines two paths into one.
#Note: Still not sure if it should be And or =>
def createSinglePath(t, s, sig):
    pre = t.getAndTrace(sig)
    post = s.getAndTrace(sig)
    #return pre
    return "And( "+pre+", "+post+")"
    #return "Or( Not("+pre+"), "+post+")"

def getInitialVariablesUsedMap():
    variablesUsedMap = {}
    variablesUsedMap["And"] = And
    variablesUsedMap["Or"] = Or
    variablesUsedMap["Not"] = Not
    return variablesUsedMap


#Should push the pairing for a single trace t
def bigPush(s, t, secondTraces, rhs, variablesUsed, traceNum):
    sig = "t"+str(traceNum)
    print("Signature "+sig)
    bigOne = ""
    available = []  ##This represents all of the variables that are around the hole\
    variablesUsedMap = getInitialVariablesUsedMap()

    #This statement is awkward, but basically available will hold all variables before
    ##the hole so it can be used by the grammers
    available = stitch(t, rhs, variablesUsed, sig)
    bigOne = createSinglePath(t, secondTraces[0], sig)
    
    i = 1
    while(i<len(secondTraces)):
        bigOne = "Or("+createSinglePath(t, secondTraces[i], sig)+","+bigOne+")"
        i = i +1

    #Not for final, assumes only have 1 post: What?
    variablesUsedMap = createAllUsedVariablesMap(variablesUsedMap, variablesUsed, sig)

    #Evaluate and push onto solver
    print("Big One:")
    print(bigOne)
    print("\n\n\n\n")

    print("Variables used:" + str(variablesUsedMap))
    s.add((eval(bigOne, {}, variablesUsedMap)))
    s.push()
    print(s)

    return available

#Pairs the variables of the two with each other so xPreHole == xf1
#Returns all of the variables around the hole
def stitch(preHole, rhs, variablesUsed, sig):
    return preHole.stitchIt(rhs, variablesUsed, sig)

##Should return an answer of the form ("sat", "answer") or ("unsat", "")
def grammar1(rhs, s, available):
    #s.pop() only one that doesn't do this
    parse = {}
    parse["hole"] = Int("hole")
    for trace in available:
        currentMap = available[trace]
        hold = currentMap["rhs"]
        parse[hold] = Int(hold)
        s.add(eval(hold+" == hole", {}, parse))

    if(str(s.check())=="sat"):
        done = True
        m = s.model()
        ans = m[Int("hole")]

        return ("sat",rhs+"="+str(ans))
    else:
        return ("unsat", "")
    

def grammar2(rhs, s, available):
    s.pop()
    i = 0


traceFile = "/Users/jessemiller/Desktop/Research/MattSebastian/Projects/HCC/CurrentTests/Mattsproject/randoopscripts/traces.txt"
errorLine = "16"

##Assume that variables have the form xf1 (st = secondary trace)
secondaryTrace = "/Users/jessemiller/Desktop/Research/MattSebastian/Projects/HCC/CurrentTests/Mattsproject/randoopscripts/bottomtraces.txt"
outputfile = ""

preconditions = ["x < 100"]
postconditions = ["retf == 20"]

#Start the actual program
rhs = "x"

#The map of variables that will be added to throughout the program

s = Solver()
variablesUsed = []

##Get the initial traces
arr = getIndividualPaths(traceFile)
print("Individual Paths: "+str(arr))
#Slice the traces so that only the ones having to do with the errorLine are returned and only the values up to that line are returned
preBug = getUpToBug(errorLine, arr)
print("PreBug: "+str(preBug))

#Get all of the variables and constraints from the preconditions
firstTraces = []
for p in preBug:
    newpreconditions, variablesUsed = getConstraints(preconditions, variablesUsed)
    ftrace, variablesUsed  = getConstraints(p, variablesUsed)
    ftrace.weavePre(newpreconditions)
    ftrace.raisePreConditions(variablesUsed)
    firstTraces.append(ftrace)
print("First Traces: ")
for t in firstTraces:
    print(t.toString())
print("\n\n\n")

#Get the secondary traces
postBug = getIndividualPaths(secondaryTrace)
secondTraces = []
for p in postBug:
    newpostconditions, variablesUsed = getConstraints(postconditions, variablesUsed)
    p = loseLineNumbers(p)
    strace, variablesUsed = getConstraints(p, variablesUsed)
    strace.weavePost(newpostconditions)
    secondTraces.append(strace)


print("Bottom Traces: ")
for t in secondTraces:
    print(t.toString())
print("\n\n\n")

#Get the intial stuff inserted and stitched
available = {}
for t in range(0, len(firstTraces)):
    arr = bigPush(s, firstTraces[t], secondTraces, rhs, variablesUsed, t)
    available[t]=arr

#At this point, available should be a map, going from each trace number to all the available values
print(available)
#Try Various Grammars  
soFar = "unsat"
ans =""

print(s)

if(soFar == "unsat"):
    print("Trying grammar1")
    soFar, ans = grammar1(rhs, s, available)

if(soFar == "unsat"):
    print("Trying grammar2")
    soFar, ans = grammar2(rhs, s, available)

if(soFar == "sat"):
    print("It worked")
    print(ans)
else:
    print("It didn't work")


