import java.awt.Image;
import java.awt.Color;
import java.awt.image.ImageObserver;
import java.awt.Polygon;
import java.text.AttributedCharacterIterator;
import java.awt.Shape;
import java.awt.Rectangle;
import java.awt.Font;
import java.awt.FontMetrics;

class Graphics
{
    void clearRect(int x, int y, int width, int height) {}
    void clipRect(int x, int y, int width, int height) {}
    void copyArea(int x, int y, int width, int height, int dx, int dy) {}
    Graphics create() { return null; }
    Graphics create(int x, int y, int width, int height) { return null; }
    void dispose() {}
    void draw3DRect(int x, int y, int width, int height, boolean raised) {}
    void drawArc(int x, int y, int width, int height, int startAngle, int arcAngle) {}
    void drawBytes(byte[] data, int offset, int length, int x, int y) {}
    void drawChars(char[] data, int offset, int length, int x, int y) {}
    boolean drawImage(Image img, int x, int y, Color bgcolor, ImageObserver observer) { return true; }
    boolean drawImage(Image img, int x, int y, ImageObserver observer) { return true; }
    boolean drawImage(Image img, int x, int y, int width, int height, Color bgcolor, ImageObserver observer) { return true; }
    boolean drawImage(Image img, int x, int y, int width, int height, ImageObserver observer) { return true; }
    boolean drawImage(Image img, int dx1, int dy1, int dx2, int dy2, int sx1, int sy1, int sx2, int sy2, Color bgcolor, ImageObserver observer) { return true; }
    boolean drawImage(Image img, int dx1, int dy1, int dx2, int dy2, int sx1, int sy1, int sx2, int sy2, ImageObserver observer) { return true; }
    void drawLine(int x1, int y1, int x2, int y2) {}
    void drawOval(int x, int y, int width, int height) {}
    void drawPolygon(int[] xPoints, int[] yPoints, int nPoints) {}
    void drawPolygon(Polygon p) {}
    void drawPolyline(int[] xPoints, int[] yPoints, int nPoints) {}
    void drawRect(int x, int y, int width, int height) {}
    void drawRoundRect(int x, int y, int width, int height, int arcWidth, int arcHeight) {}
    void drawString(AttributedCharacterIterator iterator, int x, int y) {}
    void drawString(String str, int x, int y) {}
    void fill3DRect(int x, int y, int width, int height, boolean raised) {}
    void fillArc(int x, int y, int width, int height, int startAngle, int arcAngle) {}
    void fillOval(int x, int y, int width, int height) {}
    void fillPolygon(int[] xPoints, int[] yPoints, int nPoints) {}
    void fillPolygon(Polygon p) {}
    void fillRect(int x, int y, int width, int height) {}
    void fillRoundRect(int x, int y, int width, int height, int arcWidth, int arcHeight) {}
    Shape getClip() { return null; }
    Rectangle getClipBounds() { return null; }
    Rectangle getClipBounds(Rectangle r) { return null; }
    Rectangle getClipRect() { return null; }
    Color getColor() { return new Color(0, 0, 0); }
    Font getFont() { return null; }
    FontMetrics getFontMetrics() { return null; }
    boolean hitClip(int x, int y, int width, int height) { return false; }
    void setClip(int x, int y, int width, int height) {}
    void setClip(Shape clip) {}
    void setColor(Color c) {}
    void setFont(Font font) {}
    void setPaintMode() {}
    void setXORMode(Color c1) {}
    void translate(int x, int y) {}
}

