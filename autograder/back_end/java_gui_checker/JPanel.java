import java.awt.Font;
import java.awt.event.KeyListener;
import java.awt.event.MouseListener;
import java.awt.event.MouseMotionListener;
import java.awt.event.MouseWheelListener;

class JPanel
{
    int width;
    int height;

    JPanel()
    {
        this.width = 1600;
        this.height = 900;
    }

    int getWidth()
    {
        return this.width;
    }

    int getHeight()
    {
        return this.height;
    }

    void paintComponent()
    {
    }

    void repaint()
    {
        this.paintComponent();
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
