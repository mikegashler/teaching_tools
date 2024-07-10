import java.util.Map;
import java.awt.Shape;
import java.awt.font.GlyphVector;
import java.awt.Component;
import java.text.AttributedCharacterIterator;
import java.awt.RenderingHints;
import java.awt.image.RenderedImage;
import java.awt.GraphicsConfiguration;
import java.awt.Stroke;
import java.awt.Paint;
import java.awt.image.BufferedImage;
import java.awt.image.BufferedImageOp;
import java.awt.image.renderable.RenderableImage;
import java.awt.geom.AffineTransform;
import java.awt.Image;
import java.awt.image.ImageObserver;
import java.awt.Color;
import java.awt.Rectangle;
import java.awt.Composite;
import java.awt.font.FontRenderContext;

class Graphics2D extends Graphics
{
    void addRenderingHints(Map<?,?> hints) {}
    void clip(Shape s) {}
    void draw(Shape s) {}
    void draw3DRect(int x, int y, int width, int height, boolean raised) {}
    void drawGlyphVector(GlyphVector g, float x, float y) {}
    void drawImage(BufferedImage img, BufferedImageOp op, int x, int y) {}
    boolean drawImage(Image img, AffineTransform xform, ImageObserver obs) { return true; }
    void drawRenderableImage(RenderableImage img, AffineTransform xform) {}
    void drawRenderedImage(RenderedImage img, AffineTransform xform) {}
    void drawString(AttributedCharacterIterator iterator, float x, float y) {}
    void drawString(AttributedCharacterIterator iterator, int x, int y) {}
    void drawString(String str, float x, float y) {}
    void drawString(String str, int x, int y) {}
    void fill(Shape s) {}
    void fill3DRect(int x, int y, int width, int height, boolean raised) {}
    Color getBackground() { return new Color(0, 0, 0); }
    Composite getComposite() { return null; }
    GraphicsConfiguration getDeviceConfiguration() { return null; }
    FontRenderContext getFontRenderContext() { return null; }
    Paint getPaint() { return null; }
    Object getRenderingHint(RenderingHints.Key hintKey) { return null; }
    RenderingHints getRenderingHints() { return null; }
    Stroke getStroke() { return null; }
    AffineTransform getTransform() { return null; }
    boolean hit(Rectangle rect, Shape s, boolean onStroke) { return true; }
    void rotate(double theta) {}
    void rotate(double theta, double x, double y) {}
    void scale(double sx, double sy) {}
    void setBackground(Color color) {}
    void setComposite(Composite comp) {}
    void setPaint(Paint paint) {}
    void setRenderingHint(RenderingHints.Key hintKey, Object hintValue) {}
    void setRenderingHints(Map<?,?> hints) {}
    void setStroke(Stroke s) {}
    void setTransform(AffineTransform Tx) {}
    void shear(double shx, double shy) {}
    void transform(AffineTransform Tx) {}
    void translate(double tx, double ty) {}
    void translate(int x, int y) {}
}

