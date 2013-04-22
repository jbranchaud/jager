package sftcas;

public class TCAS {

    public static void main(String[] args) {
        TCAS tcas = new TCAS();
        tcas.is_upward_preferred(true,0,0);
    }

    public int is_upward_preferred(boolean inhibit, int up_sep, int down_sep) {
        int bias;
        if(inhibit) {
            bias = down_sep; // fix: bias=up_sep+100
        }
        else {
            bias = up_sep;
        }

        if(bias > down_sep) {
            return 1;
        }
        else {
            return 0;
        }
    }
}
