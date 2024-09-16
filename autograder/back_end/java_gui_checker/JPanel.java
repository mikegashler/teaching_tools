import java.awt.Component;
import java.awt.Font;
import java.awt.event.KeyListener;
import java.awt.event.MouseListener;
import java.awt.event.MouseMotionListener;
import java.awt.event.MouseWheelListener;
import java.util.ArrayList;

class LightWeightComponent extends Component
{
    public boolean isLightweight() { return true; }
    public boolean isDisplayable() { return false; }
};



class JPanel
{
    int width;
    int height;
    Graphics graphics;
    static LightWeightComponent click_me = new LightWeightComponent();
    public ArrayList<Component> components;

    JPanel()
    {
        this.width = 1600;
        this.height = 900;
        this.graphics = new Graphics2D();
        components = new ArrayList<Component>();
    }

    void add(Component comp) {
        components.add(comp);
    }

    void add(Component comp, String pos) {
        components.add(comp);
    }

    void add(JPanel comp) {
    }

    void add(JPanel comp, String pos) {
    }

    void setOpaque(boolean b) {}

    int getWidth()
    {
        return this.width;
    }

    int getHeight()
    {
        return this.height;
    }

    void paintComponent(Graphics g)
    {
    }

    void setFocusable(boolean b)
    {
    }

    void requestFocusInWindow()
    {
    }

    void setLayout(Object ob)
    {
    }

    void repaint()
    {
        this.paintComponent(this.graphics);
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
