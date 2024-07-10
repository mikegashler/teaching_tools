class Toolkit
{
    static Toolkit defaultToolkit = null;

    public static Toolkit getDefaultToolkit()
    {
        if (Toolkit.defaultToolkit == null)
            Toolkit.defaultToolkit = new Toolkit();
        return Toolkit.defaultToolkit;
    }

    void sync()
    {
    }
}
