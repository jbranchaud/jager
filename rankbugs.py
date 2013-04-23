import FaultLocalization

outputfile = "/Users/jessemiller/Documents/UNL/2012-13/2ndSemester/ProgramSynthesis/TermProject/jager/output/gbtraces.txt"

listBugs = FaultLocalization.rank_statements(outputfile)
print(listBugs)
