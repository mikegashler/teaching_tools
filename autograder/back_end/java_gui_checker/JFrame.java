import java.awt.Font;
import java.awt.event.KeyListener;
import java.awt.event.MouseListener;
import java.awt.event.MouseMotionListener;
import java.awt.event.MouseWheelListener;

class JFrame
{
    public static int EXIT_ON_CLOSE = 0;

    String title;
    int width;
    int height;
    JPanel panel;

    public void setName(String s)
    {
    }

    public void setTitle(String s)
    {
        this.title = s;
    }

    public void setSize(int w, int h)
    {
        this.width = w;
        this.height = h;
    }

    public void setEnabled(boolean b)
    {
    }

    public void setFocusable(boolean b)
    {
    }

    void setFont(Font f)
    {
    }

    public static class Container
    {
        JFrame frame;

        Container(JFrame frame)
        {
            this.frame = frame;
        }

        public void add(JPanel panel)
        {
            this.frame.panel = panel;
        }
    };

    public Container getContentPane()
    {
        return new Container(this);
    }

    public void setDefaultCloseOperation(int operation)
    {
    }

    public void setVisible(boolean b)
    {
    }

    public void addKeyListener(KeyListener l)
    {
    }

    public void addMouseListener(MouseListener l)
    {
    }

    public void addMouseMotionListener(MouseMotionListener l)
    {
    }

    public void addMouseWheelListener(MouseWheelListener l)
    {
    }
}
