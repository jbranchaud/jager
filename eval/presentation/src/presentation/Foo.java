package presentation;

public class Foo {

    public static void main(String[] args) {

        Foo f = new Foo();
        f.foo(0,0);
    }

    public int foo(int x, int y) {
        int a = x * y;
        if(a <= 0) {
            if(y < 0) {
                y = y * -1;
            }
            else {
                if( x < 0) {
                    x = x * 1; //bug
                }
            }
        }

        if(x < 0) {
            x = x * -1;
            y = y * -1;
        }

        return x + y;
    }

}
