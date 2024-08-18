import javax.swing.Action;
import javax.swing.Icon;
import java.awt.Component;
import java.awt.event.ActionListener;
import java.awt.event.ActionEvent;

class JButton extends Component
{
    public String text;
    public ActionListener listener;

    JButton() {
        this.text = "";
    }

    JButton(String text) {
        this.text = text;
    }

    void push() {
        System.out.println("[autograder] Pushing button: '" + this.text + "'");
        this.listener.actionPerformed(new ActionEvent(this, 0, ""));
    }

    void setText(String text) {
        this.text = text;
    }

    String getText() {
        return this.text;
    }

    void addActionListener(ActionListener listener) {
        this.listener = listener;
    }

    public void setVisible(boolean b) {}
    public void setEnabled(boolean b) {}
    public void setFocusable(boolean b) {}
}
