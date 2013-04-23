package gov.nasa.jpf.symbc.listeners;

import gov.nasa.jpf.Config;
import gov.nasa.jpf.JPF;
import gov.nasa.jpf.ListenerAdapter;
import gov.nasa.jpf.jvm.ChoiceGenerator;
import gov.nasa.jpf.jvm.JVM;
import gov.nasa.jpf.jvm.SystemState;
import gov.nasa.jpf.jvm.bytecode.BIPUSH;
import gov.nasa.jpf.jvm.bytecode.GOTO;
import gov.nasa.jpf.jvm.bytecode.IADD;
import gov.nasa.jpf.jvm.bytecode.ICONST;
import gov.nasa.jpf.jvm.bytecode.IDIV;
import gov.nasa.jpf.jvm.bytecode.IFEQ;
import gov.nasa.jpf.jvm.bytecode.IFGE;
import gov.nasa.jpf.jvm.bytecode.IFGT;
import gov.nasa.jpf.jvm.bytecode.IFLE;
import gov.nasa.jpf.jvm.bytecode.IFLT;
import gov.nasa.jpf.jvm.bytecode.IFNE;
import gov.nasa.jpf.jvm.bytecode.IF_ICMPEQ;
import gov.nasa.jpf.jvm.bytecode.IF_ICMPGE;
import gov.nasa.jpf.jvm.bytecode.IF_ICMPGT;
import gov.nasa.jpf.jvm.bytecode.IF_ICMPLE;
import gov.nasa.jpf.jvm.bytecode.IF_ICMPLT;
import gov.nasa.jpf.jvm.bytecode.IF_ICMPNE;
import gov.nasa.jpf.jvm.bytecode.IINC;
import gov.nasa.jpf.jvm.bytecode.ILOAD;
import gov.nasa.jpf.jvm.bytecode.IMUL;
import gov.nasa.jpf.jvm.bytecode.IRETURN;
import gov.nasa.jpf.jvm.bytecode.ISTORE;
import gov.nasa.jpf.jvm.bytecode.ISUB;
import gov.nasa.jpf.jvm.bytecode.IfInstruction;
import gov.nasa.jpf.jvm.bytecode.Instruction;
import gov.nasa.jpf.jvm.bytecode.RETURN;
import gov.nasa.jpf.report.ConsolePublisher;
import gov.nasa.jpf.report.Publisher;
import gov.nasa.jpf.search.Search;
import gov.nasa.jpf.symbc.SymbolicInstructionFactory;
import gov.nasa.jpf.symbc.bytecode.BytecodeUtils;
import gov.nasa.jpf.symbc.concolic.PCAnalyzer;
import gov.nasa.jpf.symbc.numeric.PCChoiceGenerator;
import gov.nasa.jpf.symbc.numeric.PathCondition;
import gov.nasa.jpf.symbc.numeric.SymbolicConstraintsGeneral;

import java.io.FileNotFoundException;
import java.io.PrintWriter;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.Map;
import java.util.Vector;

public class TargetedSE extends ListenerAdapter{

	Config confFile;

	LinkedList<String> s;
	
	int startLine;
	
	String adder;
	
	PrintWriter pw;
	
	boolean primed;

	// custom marker to mark error strings in method sequences

	/*
	 * If want to output whole program then just sent startLine to first line of program
	 */
	public TargetedSE(Config conf, JPF jpf) {
		jpf.addPublisherExtension(ConsolePublisher.class, this);
		confFile = conf;
		startLine = BytecodeUtils.getErrorLineNumber(conf);
		pw = null;
		if(startLine>=0){
			adder="f";
		}else{
			adder="";
		}
		primed = false;
	}


	public void stateAdvanced(Search search) {
		super.stateAdvanced(search);
		if (search.isEndState()) {
			JVM vm = search.getVM();
			SystemState ss = vm.getSystemState();

			ChoiceGenerator<?> [] cgs = ss.getChoiceGenerators();
			Map<String, Integer> ssa = new HashMap<String, Integer>();


			Instruction [] code = getCode(cgs);
			int next;
			int i = 0;

			s = new LinkedList<String>();
			
			primed = false;
			
			BooleanPointer printIt = new BooleanPointer(false);

			next = printBlock(code, 0, ssa, printIt);
			while(next>=0){
				Instruction currentInstruction = code[next];
				if(currentInstruction instanceof IfInstruction){
					IfInstruction currentIf = (IfInstruction)currentInstruction;
					boolean conditionalValue = currentIf.getConditionValue();
					//System.out.println(currentIf.toString()+" "+conditionalValue+" "+currentIf.isBackJump());
					//System.out.println(currentInstruction.getClass());

					handleIfStatement(currentIf, conditionalValue, ssa, printIt);

					if(conditionalValue){
						next = currentIf.getTarget().getInstructionIndex();
					}else{
						next = currentIf.getInstructionIndex() + 1;
					}
					i = i + 1;
					next = printBlock(code, next, ssa, printIt);
				}                   

			}
			this.printToFile(s, printIt);
		}
	}
	
	public void publishStart (Publisher publisher) {
		String outfile = BytecodeUtils.geJagerWrite(confFile);
		try {
			pw = new PrintWriter(outfile);
		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
	
	public void publishFinished (Publisher publisher) {
		pw.close();
	}
	
	private void printToFile(LinkedList<String> list, BooleanPointer printIt){
		if(printIt.getValue()||startLine<0){
			pw.println("\n\n\n\n");
			pw.println("********************");
			while(!s.isEmpty()){
				pw.println(s.removeLast());
				//System.out.println(s.removeLast());
			}
			pw.flush();
		}
	}
	
	/**
	 * The goal here is to symbolically explore all paths following the bug which occurs
	 * on line startLine.  In order to do this, after this instruction is executed, the
	 * path condition is cleared to allow exploration of every possible path beginning with
	 * that statement.  The path is not always cleared so that infeasible paths that occur
	 * after the error are removed from consideration.
	 * 
	 *  A CFG in this case is optimum since no solving is needed to generate these paths.
	 *  This last statement might not be true because there could be infeasible paths that
	 *  occur along the way.  What would be best is to have a single path get to the instruction
	 *  we desire and then fully explore all paths.  There is no other need to explore, although
	 *  this current implementation doesn't stop it.
	 */
	public void instructionExecuted(JVM vm) {
		if (!vm.getSystemState().isIgnored()) {
			SystemState ss = vm.getSystemState();
			Instruction insn = vm.getLastInstruction();

			//If going to start doing loops than final boolean statement in this if will require a lot more thought
			if (insn!= null && insn.getSourceLocation()!=null &&insn.getLineNumber()==startLine) {
				if(BytecodeUtils.isMemberClassUnderTest(confFile, insn.getSourceLocation())){
					//System.out.println("\n\n\n\n\n");

					ChoiceGenerator<?> cg = ss.getChoiceGenerator();

					if (!(cg instanceof PCChoiceGenerator)){
						ChoiceGenerator<?> prev_cg = cg.getPreviousChoiceGenerator();
						while (!((prev_cg == null) || (prev_cg instanceof PCChoiceGenerator))) {
							prev_cg = prev_cg.getPreviousChoiceGenerator();
						}
						cg = prev_cg;
					}
					if ((cg instanceof PCChoiceGenerator) && ((PCChoiceGenerator) cg).getCurrentPC() != null){
						((PCChoiceGenerator)cg).setCurrentPC(new PathCondition());
					}
				}
			}
		}
	}



	private void handleIfStatement(IfInstruction currentIf, boolean conditionalValue, Map<String, Integer> ssa, BooleanPointer printIt){
		//Means Integer LT 0
		if(primed && printIt.getValue()==false&&currentIf.getLineNumber()!=startLine){
			printIt.setValue(true);
			ssa.clear();
			s.clear();
		}
		
		if(currentIf.getLineNumber()==startLine && !primed){
			primed = true;
		}
			

		
		if(currentIf instanceof IFLT){
			//                                System.out.println((((IFLT)currentIf)));

			String i1 = s.pop();

			if(conditionalValue){
				s.push(i1+" < 0");
			}else{
				s.push(i1+" >= 0");
			}
		}
		if(currentIf instanceof IFEQ){
			//                                System.out.println((((IFEQ)currentIf)));

			String i1 = s.pop();

			if(conditionalValue){
				s.push(i1+" == 0");
			}else{
				s.push(i1+" != 0");
			}
		}
		if(currentIf instanceof IFGT){
			//                                System.out.println((((IFGT)currentIf)));

			String i1 = s.pop();

			if(conditionalValue){
				s.push(i1+" > 0");
			}else{
				s.push(i1+" <= 0");
			}
		}
		if(currentIf instanceof IFGE){
			//                                System.out.println((((IFGE)currentIf)));

			String i1 = s.pop();

			if(conditionalValue){
				s.push(i1+" >= 0");
			}else{
				s.push(i1+" < 0");
			}
		}
		if(currentIf instanceof IFLE){
			//                                System.out.println((((IFLE)currentIf)));

			String i1 = s.pop();

			if(conditionalValue){
				s.push(i1+" <= 0");
			}else{
				s.push(i1+" > 0");
			}
		}
		if(currentIf instanceof IFNE){
			//                                System.out.println((((IFNE)currentIf)));

			String i1 = s.pop();

			if(conditionalValue){
				s.push(i1+" != 0");
			}else{
				s.push(i1+" == 0");
			}
		}
		if(currentIf instanceof IF_ICMPGE){
			//                                System.out.println((((IF_ICMPGE)currentIf)));

			String i2 = s.pop();
			String i1 = s.pop();

			if(conditionalValue){
				s.push(i1+" >= "+i2);
			}else{
				s.push(i1+" < "+i2);
			}
		}
		if(currentIf instanceof IF_ICMPGT){
			//                                System.out.println((((IF_ICMPGT)currentIf)));

			String i2 = s.pop();
			String i1 = s.pop();

			if(conditionalValue){
				s.push(i1+" > "+i2);
			}else{
				s.push(i1+" <= "+i2);
			}
		}
		if(currentIf instanceof IF_ICMPLE){
			//                                System.out.println((((IF_ICMPLE)currentIf)));

			String i2 = s.pop();
			String i1 = s.pop();

			if(conditionalValue){
				s.push(i1+" <= "+i2);
			}else{
				s.push(i1+" > "+i2);
			}
		}
		if(currentIf instanceof IF_ICMPLT){
			//                                System.out.println((((IF_ICMPLT)currentIf)));

			String i2 = s.pop();
			String i1 = s.pop();

			if(conditionalValue){
				s.push(i1+" < "+i2);
			}else{
				s.push(i1+" >= "+i2);
			}
		}
		if(currentIf instanceof IF_ICMPNE){
			//                                System.out.println((((IF_ICMPNE)currentIf)));

			String i2 = s.pop();
			String i1 = s.pop();

			if(conditionalValue){
				s.push(i1+" != "+i2);
			}else{
				s.push(i1+" == "+i2);
			}
		}
		if(currentIf instanceof IF_ICMPEQ){
			//                                System.out.println((((IF_ICMPEQ)currentIf)));

			String i2 = s.pop();
			String i1 = s.pop();

			if(conditionalValue){
				s.push(i1+" = "+i2);
			}else{
				s.push(i1+" != "+i2);
			}
		}
		String str = s.pop();
		str = str+", "+currentIf.getLineNumber();
		s.push(str);
	}

	private int printBlock(Instruction [] code, int pc, Map<String, Integer> ssa, BooleanPointer printIt){
		int i = pc;
		while(i>=0 && i<code.length && code[i]!=null && !code[i].toString().contains("if")){
			if(primed && printIt.getValue()==false && code[i].getLineNumber()!=startLine){
				printIt.setValue(true);
				s.clear();
				ssa.clear();
			}
			
			if(code[i].getLineNumber()==startLine){
				primed = true;
			}
			//System.out.println(code[i].toString());

			if(code[i] instanceof ICONST){
				//			System.out.println((((ICONST)code[i]).getValue()));
				s.push(Integer.toString(((ICONST)code[i]).getValue()));
			}
			if(code[i] instanceof BIPUSH){
				//			System.out.println((((BIPUSH)code[i]).getValue()));
				s.push(Integer.toString((((BIPUSH)code[i]).getValue())));
			}
			if(code[i] instanceof ISTORE){
				//			System.out.println((((ISTORE)code[i]).getLocalVariableName()));
				String varName = ((ISTORE)code[i]).getLocalVariableName() + adder;

				String ssaVar;
				if(!ssa.containsKey(varName)){
					ssa.put(varName, new Integer(1));
				}
				ssaVar = varName + (ssa.get(varName)+1);
				ssa.put(varName, ssa.get(varName)+1);
				String string = s.pop();
				s.push(ssaVar+" == "+string+", "+code[i].getLineNumber());
			}
			
			if(code[i] instanceof ILOAD){
				//			System.out.println((((ILOAD)code[i]).getLocalVariableName()));
				String varName = ((ILOAD)code[i]).getLocalVariableName() + adder;
				if(!ssa.containsKey(varName)){
					ssa.put(varName, new Integer(1));
				}
				s.push(varName+ssa.get(varName));
			}
			if(code[i] instanceof IINC){
				//			System.out.println((((IINC)code[i]).getIncrement()));
				int index = ((IINC)code[i]).getIndex();
				int where = code[i].getPosition();
				//			System.out.println(code[i].getMethodInfo().getLocalVar(index, where).getName());

				String varName = code[i].getMethodInfo().getLocalVar(index, where).getName() + adder;

				String ssaVar;
				String preSetVar;
				if(!ssa.containsKey(varName)){
					ssa.put(varName, new Integer(1));
				}
				preSetVar = varName+ssa.get(varName);
				ssaVar = varName +(ssa.get(varName)+1);
				
				s.push(ssaVar+" == "+preSetVar+" + "+(((IINC)code[i]).getIncrement())+", "+code[i].getLineNumber());
				ssa.put(varName, ssa.get(varName)+1);
			}

			if(code[i] instanceof IRETURN){
				String i1 = s.pop();
				s.push("ret == "+i1+", "+code[i].getLineNumber());
				return -1;
			}

			if(code[i] instanceof RETURN){
				return -1;
			}

			//Pops 2 and pushes
			if(code[i] instanceof IMUL){
				String i2 = s.pop();
				String i1 = s.pop();

				if(multipleParts(i1)){
					i1 = "("+i1+")";
				}

				if(multipleParts(i2)){
					i2 = "("+i2+")";
				}
				s.push(i1+" * "+i2);
			}

			if(code[i] instanceof IADD){
				String i2 = s.pop();
				String i1 = s.pop();

				s.push(i1+" + "+i2);
			}

			if(code[i] instanceof ISUB){
				String i2 = s.pop();
				String i1 = s.pop();

				s.push(i1+" - "+i2);
			}

			if(code[i] instanceof IDIV){
				String i2 = s.pop();
				String i1 = s.pop();

				if(multipleParts(i1)){
					i1 = "("+i1+")";
				}

				if(multipleParts(i2)){
					i2 = "("+i2+")";
				}
				
				s.push(i1+" / "+i2);
			}

			if(code[i] instanceof GOTO){
				i = ((GOTO)code[i]).getTarget().getInstructionIndex();
			}else{
				i++;
			}
		}
		return i;
	}
	
	private boolean multipleParts(String s){
		int startParen = s.indexOf("(");
		//If there are parentheses, but it isn't the first character then need more parens
		if(startParen>0){
			return true;
		}
		
		//If there aren't any parens
		if(startParen==-1){
			//If there are spaces then need parens
			if(s.contains(" ")){
				return true;
			}
			//Otherwise a single character so no need for parens
			return false;
		}
		
		//Otherwise see how far the first parentheses goes
		int lparen = 0;
		int i = 0;
		while(i<s.length()&&(s.charAt(i)!=')'||lparen!=1)){
			if(s.charAt(i)=='('){
				lparen ++;
			}
			if(s.charAt(i)==')'){
				lparen --;
			}
			i++;
		}
		//If there is more left after then end of the first parens
		if(i<s.length()){
			return true;
		}
		return false;
		//return s.substring(0, i+1);
	}

	private Instruction [] getCode(ChoiceGenerator<?> [] cgs){
		for(int i=0; i<cgs.length; i++){
			ChoiceGenerator<?> cg = cgs[i];
			if ((cg instanceof PCChoiceGenerator)){
				Instruction insn = ((PCChoiceGenerator)cg).getInsn();
				if(insn!=null){
					return insn.getMethodInfo().getInstructions();
				}
			}
		}
		return null;
	}
	
	private class BooleanPointer{
		private boolean value;
		private BooleanPointer(boolean value){
			this.value = value;
		}
		private void setValue(boolean value){
			this.value = value;
		}
		
		private boolean getValue(){
			return this.value;
		}
	}
}
