using System;
using System.Drawing;
using System.Windows.Forms;

internal static class CuaSmokeProgram
{
    [STAThread]
    private static void Main()
    {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        var form = new Form();
        form.Name = "CuaSmokeFixture";
        form.Text = "VelvetOS Cua Isolated GUI Smoke";
        form.ClientSize = new Size(460, 185);
        form.FormBorderStyle = FormBorderStyle.FixedDialog;
        form.MaximizeBox = false;
        form.StartPosition = FormStartPosition.CenterScreen;

        var prompt = new Label();
        prompt.Name = "PilotPrompt";
        prompt.Text = "Local smoke only. No business integration.";
        prompt.SetBounds(20, 15, 425, 24);
        var entry = new TextBox();
        entry.Name = "PilotInput";
        entry.AccessibleName = "Cua pilot input";
        entry.SetBounds(20, 48, 410, 26);
        var run = new Button();
        run.Name = "PilotCompute";
        run.AccessibleName = "Compute 6 times 7";
        run.Text = "Compute 6 x 7";
        run.SetBounds(20, 90, 160, 34);
        var output = new Label();
        output.Name = "PilotResult";
        output.AccessibleName = "Cua pilot result";
        output.Text = "Result: Ready";
        output.SetBounds(200, 96, 230, 32);
        output.AutoSize = false;
        run.Click += delegate(object sender, EventArgs e) {
            output.Text = "Result: 42";
            output.AccessibleName = "Result: 42";
            form.Text = "VelvetOS Cua Isolated GUI Smoke - 42";
        };
        form.Controls.Add(prompt);
        form.Controls.Add(entry);
        form.Controls.Add(run);
        form.Controls.Add(output);
        Application.Run(form);
    }
}
