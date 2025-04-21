/****************************************************************************
 -*- coding: utf-8 -*-
 Copyright (c) 2022 Salvador E. Tropea
 Copyright (c) 2022 Instituto Nacional de Tecnologïa Industrial
 License: GPLv3+
 Project: KiAuto (formerly kicad-automation-scripts)
 Description:
 This module implements "Function Interposition" to determine what's KiCad
 doing. The main motivation is to reduce time-out problems in the 3D
 renderer.
****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <dlfcn.h> /* header required for dlsym() */
#include <string.h>
#include <pango/pango.h>
#include <GL/glx.h>
#include <gtk/gtk.h>

/* Always log open/close activity, not just when requested */
#define FORCE_LOW_LEVEL_LOG 1
/* Log even when opening for read */
#define ALL_OPEN_MODES 1

void glXSwapBuffers(Display *dpy, GLXDrawable drawable)
{
 static void (*next_func)(Display *, GLXDrawable)=NULL;
 static int cnt=0;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping GLX\n");
    next_func=dlsym(RTLD_NEXT,"glXSwapBuffers");
    if ((msg=dlerror())!=NULL)
       printf("* dlopen failed : %s\n", msg);
   }

 next_func(dpy, drawable);
 printf("GLX:Swap %d\n", cnt++);
 fflush(stdout);
}

#define MAX_STORE 1024

void pango_layout_set_text(PangoLayout *layout, const char *text, int length)
{
 static void (*next_func)(PangoLayout *, const char *, int)=NULL;
 static char buffer[MAX_STORE];

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping PANGO\n");
    next_func=dlsym(RTLD_NEXT,"pango_layout_set_text");
    if ((msg=dlerror())!=NULL)
       printf("* dlopen failed : %s\n", msg);
    buffer[0]=0;
   }

 /* Filter what we log */
 if (text[0]!=0 &&  /* Emty strings??!! */
     !(text[0]=='g' && text[1]==0) &&   /* g seems to be used to meassure */
     !(text[0]=='.' && text[1]=='.' && text[2]=='.' && text[3]==0) &&
     !(text[0]==(char)0xE2 && text[1]==(char)0x97 && text[2]==(char)0x8F && text[3]==0) &&  /* Ball 1 */
     !(text[0]==(char)0xE2 && text[1]==(char)0x80 && text[2]==(char)0xA2 && text[3]==0) &&  /* Ball 2 */
     strcmp(text, "ABCDEFHXfgkj"))  /* To meassure? */
   {/* Avoid repetition */
    if (strncmp(text, buffer, MAX_STORE))  /* Most stuff is sent 3 times!!! */
      {
       fputs("PANGO:", stdout);
       fputs(text, stdout);
       fputc('\n', stdout);
       fflush(stdout);
      }
    strncpy(buffer, text, MAX_STORE);
   }
 return next_func(layout, text, length);
}


void gtk_window_set_title(GtkWindow *window, const gchar *title)
{
 static void (*next_func)(GtkWindow *window, const gchar *title)=NULL;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping window title change\n");
    next_func=dlsym(RTLD_NEXT,"gtk_window_set_title");
    if ((msg=dlerror())!=NULL)
       printf("* dlopen failed : %s\n", msg);
   }

 next_func(window, title);
 printf("GTK:Window Title:%s\n", title);
 fflush(stdout);
}


void gtk_window_set_modal(GtkWindow* window, gboolean modal)
{
 static void (*next_func)(GtkWindow* window, gboolean modal)=NULL;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping set modal\n");
    next_func=dlsym(RTLD_NEXT,"gtk_window_set_modal");
    if ((msg=dlerror())!=NULL)
       printf("* dlopen failed : %s\n", msg);
   }

 next_func(window, modal);
 printf("GTK:Window Set Modal:%s %d\n", gtk_window_get_title(window), modal);
 fflush(stdout);
}


void gtk_widget_show(GtkWidget* widget)
{
 static void (*next_func)(GtkWidget* widget)=NULL;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping widget show\n");
    next_func=dlsym(RTLD_NEXT,"gtk_widget_show");
    if ((msg=dlerror())!=NULL)
       printf("* dlopen failed : %s\n", msg);
   }

 next_func(widget);
 if (GTK_IS_WINDOW(widget))
    printf("GTK:Window Show:%s\n", gtk_window_get_title(GTK_WINDOW(widget)));
 /*else
    printf("GTK:Window Show:Widget:%s\n", gtk_widget_get_name(widget));*/
 fflush(stdout);
}


void gtk_button_set_label(GtkButton* button, const char *label)
{
 static void (*next_func)(GtkButton* button, const char *label)=NULL;
 const char *ori=label;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping button label\n");
    next_func=dlsym(RTLD_NEXT,"gtk_button_set_label");
    if ((msg=dlerror())!=NULL)
       printf("* dlopen failed : %s\n", msg);
   }

 /* ACEGLP */
 if (g_strcmp0(label, "Print")==0)
    /* Why KiCad people hates shortcuts? */
    label="_Print";
 else if (label[0]=='S' && label[1]=='a' && label[2]=='v' && label[3]=='e')
    label="_Save";
 else if (g_strcmp0(label, "Plot Current Page")==0)
    label="Plot _Current Page";
 else if (g_strcmp0(label, "Plot All Pages")==0)
    label="Plot _All Pages";
 else if (g_strcmp0(label, "Generate Netlist")==0 || g_strcmp0(label, "Export Netlist")==0)
    label="_Export Netlist";
 else if (g_strcmp0(label, "Close")==0)
    label="C_lose";
 else if (g_strcmp0(label, "Generate")==0)
    label="_Generate";
 else if (g_strcmp0(label, "Auto-Match Layers")==0)
    /* KiCad 9 importing Altium files, asking to confirm the layer mapping */
    label="Auto-Match _Layers";
 next_func(button, label);
 printf("GTK:Button Label:%s\n", label);
 if (label!=ori)
    printf("GTK:Button Label:**Changed from %s\n", ori);
 fflush(stdout);
}

gchar *dir_name="/tmp";
gchar *base_name="pp";
gchar *format="pdf";

/*
  Loads the print options from a file named "interposer_options.txt". I.e:
/tmp
pp
pdf
*/
void load_print_options()
{
 GIOChannel *f;
 gchar *line;
 gsize length, terminator_pos;
 char *fn;

 fn=getenv("KIAUTO_INTERPOSER_PRINT");
 if (fn==NULL)
   {
    printf("GTK:Error:KIAUTO_INTERPOSER_PRINT not defined\n");
    return;
   }
 printf("GTK:Read:Dir_Name:%s\n", dir_name);
 f=g_io_channel_new_file(fn, "r", NULL);
 if (f==NULL)
   {
    printf("GTK:Error:Unable to load %s\n", fn);
    return;
   }
 g_io_channel_read_line(f, &dir_name, &length, &terminator_pos, NULL);
 dir_name[terminator_pos]=0;
 printf("GTK:Read:Dir_Name:%s\n", dir_name);
 g_io_channel_read_line(f, &base_name, &length, &terminator_pos, NULL);
 base_name[terminator_pos]=0;
 printf("GTK:Read:Base_Name:%s\n", base_name);
 g_io_channel_read_line(f, &format, &length, &terminator_pos, NULL);
 format[terminator_pos]=0;
 printf("GTK:Read:Format:%s\n", format);
 g_io_channel_unref(f);
}


/*
  Forces the GTK print dialog to select the output file, format and printer we want
*/
GtkPrintOperationResult gtk_print_operation_run(GtkPrintOperation* op, GtkPrintOperationAction action, GtkWindow* parent, GError** error)
{
 static GtkPrintOperationResult (*next_func)(GtkPrintOperation* , GtkPrintOperationAction , GtkWindow* , GError** )=NULL;
 GtkPrintOperationResult res;
 GtkPrintSettings *print_sets;
 GtkSettings *gtk_sets;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping print op run\n");
    next_func=dlsym(RTLD_NEXT,"gtk_print_operation_run");
    if ((msg=dlerror())!=NULL)
       printf("* dlopen failed : %s\n", msg);
    load_print_options();
   }

 print_sets = gtk_print_operation_get_print_settings(op);
 /* Select the file format and name */
 gtk_print_settings_set(print_sets, GTK_PRINT_SETTINGS_OUTPUT_BASENAME, base_name);
 gtk_print_settings_set(print_sets, GTK_PRINT_SETTINGS_OUTPUT_DIR, dir_name);
 gtk_print_settings_set(print_sets, GTK_PRINT_SETTINGS_OUTPUT_FILE_FORMAT, format);
 /* Choose the "Print to File" printer */
 gtk_print_settings_set_printer(print_sets, "Print to File");
 /* Restrict the backends to "file", otherwise the default printer will prevail */
 gtk_sets = gtk_settings_get_default();
 g_object_set(gtk_sets, "gtk-print-backends", "file", NULL);

 /* Now run the dialog. Lamentably GTK_PRINT_OPERATION_ACTION_PRINT can't be used. IMHO a bug */
 res = next_func(op, action, parent, error);
 printf("GTK:Print Run:%s\n", gtk_window_get_title(parent));

 fflush(stdout);
 return res;
}


void gtk_label_set_text_with_mnemonic(GtkLabel *label, const gchar *str)
{
 static void (*next_func)(GtkLabel *label, const gchar *str)=NULL;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping label set text\n");
    next_func=dlsym(RTLD_NEXT,"gtk_label_set_text_with_mnemonic");
    if ((msg=dlerror())!=NULL)
       printf("* dlopen failed : %s\n", msg);
   }

 /* Create some accelerators to make the navigation easier */
  /* DRC Control dialog */
 if (g_strcmp0(str, "Report all errors for tracks (slower)")==0)
    str="_Report all errors for tracks (slower)";
 else if (g_strcmp0(str, "Create report file:")==0)
    str="_Create report file:";
  /* GenCad export dialog */
 else if (g_strcmp0(str, "Flip bottom footprint padstacks")==0)
    str="_Flip bottom footprint padstacks";
 else if (g_strcmp0(str, "Generate unique pin names")==0)
    str="_Generate unique pin names";
 else if (g_strcmp0(str, "Generate a new shape for each footprint instance (do not reuse shapes)")==0)
    str="Generate a _new shape for each footprint instance (do not reuse shapes)";
 else if (g_strcmp0(str, "Use drill/place file origin as origin")==0 ||
          g_strcmp0(str, "Use auxiliary axis as origin")==0)  /* KiCad 5 version */
    str="_Use drill/place file origin as origin";
 else if (g_strcmp0(str, "Save the origin coordinates in the file")==0)
    str="_Save the origin coordinates in the file";
  /* VRML export dialog */
 /* Doesn't work ... all is broken ...
 else if (g_strcmp0(str, "Footprint 3D model path:")==0)
    str="_Footprint 3D model path:";*/
  /* File menu */
 else if (g_strcmp0(str, "Export")==0)
    str="E_xport";
 else if (g_strcmp0(str, "GenCAD...")==0)
    str="_GenCAD...";
 else if (g_strcmp0(str, "VRML...")==0)
    str="_VRML...";
 else if (g_strcmp0(str, "IPC-D-356 Netlist File...")==0)
    str="_IPC-D-356 Netlist File...";
  /* EEschema Plot Schematic Options */
 else if (g_strcmp0(str, "Output directory:")==0)
    str="_Output directory:";
  /* EEschema Bill of Material */
 else if (g_strcmp0(str, "Command line running the generator:")==0)
    str="C_ommand line running the generator:";
 else if (g_strcmp0(str, "Command line:")==0)
    str="C_ommand line:";
  /* EEschema Electrical Rules Checker */
 else if (g_strcmp0(str, "Create ERC file report")==0)
    str="_Create ERC file report";

 next_func(label, str);

 printf("GTK:Label Set Text 2:%s\n", str);
 fflush(stdout);
}


gchar *gtk_file_chooser_get_filename(GtkFileChooser *chooser)
{
 static gchar *(*next_func)(GtkFileChooser *)=NULL;
 static char *fn;
 gchar *res;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping file chooser get filename\n");
    next_func=dlsym(RTLD_NEXT,"gtk_file_chooser_get_filename");
    if ((msg=dlerror())!=NULL)
       printf("* dlopen failed : %s\n", msg);
    fn=getenv("KIAUTO_INTERPOSER_FILENAME");
    if (fn==NULL)
       printf("****** NOT DEFINED\n");
   }

 res=next_func(chooser);

 if (fn!=NULL)
   {
    printf("GTK:Filename:%s\n", fn);
    printf("GTK:Filename:**Changed from %s\n",res);
    res=g_strdup(fn);
   }
 else
   {
    printf("GTK:Filename:%s\n", res);
   }
 fflush(stdout);
 return res;
}


FILE *fopen64(const char *filename, const char *mode)
{
 static FILE *(*next_func)(const char *, const char *)=NULL;
 FILE *res;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping fopen64\n");
    next_func=dlsym(RTLD_NEXT,"fopen64");
    if ((msg=dlerror())!=NULL)
       printf("* dlopen failed : %s\n", msg);
   }

 res=next_func(filename, mode);

 if (mode[0]=='w' || ALL_OPEN_MODES)
    printf("IO:open:%s\n", filename);
    if (ALL_OPEN_MODES)
       printf("IO:fopen64:%s\n", mode);
 fflush(stdout);
 return res;
}


FILE *fopen(const char *filename, const char *mode)
{
 static FILE *(*next_func)(const char *, const char *)=NULL;
 FILE *res;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping fopen\n");
    next_func=dlsym(RTLD_NEXT,"fopen");
    if ((msg=dlerror())!=NULL)
       printf("* dlopen failed : %s\n", msg);
   }

 res=next_func(filename, mode);

 if (mode[0]=='w' || ALL_OPEN_MODES)
    printf("IO:open:%s\n", filename);
    if (ALL_OPEN_MODES)
       printf("IO:fopen:%s\n", mode);
 fflush(stdout);
 return res;
}


int fclose(FILE *stream)
{
 static int(*next_func)(FILE *)=NULL;
 int res;
 char path[1024];
 char result[1024];
 int fd;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping fclose\n");
    next_func=dlsym(RTLD_NEXT,"fclose");
    if ((msg=dlerror())!=NULL)
       printf("* dlopen failed : %s\n", msg);
    printf("* next_func : %p\n", next_func);
   }

 fd=fileno(stream);
 /* Read out the link to our file descriptor. */
 sprintf(path, "/proc/self/fd/%d", fd);
 memset(result, 0, 1024);
 readlink(path, result, 1023);

 res=next_func(stream);
 printf("IO:close:%s\n",result);
 fflush(stdout);
 return res;
}


int fclose64(FILE *stream)
{
 static int(*next_func)(FILE *)=NULL;
 int res;
 char path[1024];
 char result[1024];
 int fd;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping fclose64\n");
    next_func=dlsym(RTLD_NEXT,"fclose64");
    if ((msg=dlerror())!=NULL)
       printf("* dlopen failed : %s\n", msg);
    printf("* next_func : %p\n", next_func);
   }

 fd=fileno(stream);
 /* Read out the link to our file descriptor. */
 sprintf(path, "/proc/self/fd/%d", fd);
 memset(result, 0, 1024);
 readlink(path, result, 1023);

 res=next_func(stream);
 printf("IO:close:%s\n",result);
 fflush(stdout);
 return res;
}


void gtk_main(void)
{
 static void (*next_func)(void)=NULL;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping gtk_main\n");
    next_func=dlsym(RTLD_NEXT,"gtk_main");
    if ((msg=dlerror())!=NULL)
       printf("* dlopen failed : %s\n", msg);
   }

 printf("GTK:Main:In\n");
 fflush(stdout);
 next_func();
 printf("GTK:Main:Out\n");
 fflush(stdout);
}


void gtk_widget_destroy(GtkWidget *widget)
{
 static void (*next_func)(GtkWidget *)=NULL;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    printf("* wrapping widget destroy\n");
    next_func=dlsym(RTLD_NEXT,"gtk_widget_destroy");
    if ((msg=dlerror())!=NULL)
       printf("* dlopen failed : %s\n", msg);
   }

 next_func(widget);
 if (GTK_IS_WINDOW(widget))
   {
    const char *name=gtk_window_get_title(GTK_WINDOW(widget));
    if (name)
      {
       printf("GTK:Window Destroy:%s\n", name);
       fflush(stdout);
      }
   }
}


int open64(const char *pathname, int flags, mode_t mode)
{
 static int (*next_func)(const char *, int , mode_t)=NULL;
 static int do_log=FORCE_LOW_LEVEL_LOG;
 int res;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    const char *fn;
    printf("* wrapping open64\n");
    next_func=dlsym(RTLD_NEXT,"open64");
    if ((msg=dlerror())!=NULL)
       printf("* dlopen failed : %s\n", msg);
    fn=getenv("KIAUTO_INTERPOSER_LOWLEVEL_IO");
    if ((fn==NULL || !fn[0]) && !FORCE_LOW_LEVEL_LOG)
       printf("* Not logging low level I/O\n");
    else
       do_log=1;
   }

 res=next_func(pathname, flags, mode);

 if (do_log)
   {
    printf("IO:open:%s\n", pathname);
    if (ALL_OPEN_MODES)
       printf("IO:open64:0x%X\n", mode);
    fflush(stdout);
   }
 return res;
}


int open(const char *pathname, int flags, mode_t mode)
{
 static int (*next_func)(const char *, int , mode_t)=NULL;
 static int do_log=FORCE_LOW_LEVEL_LOG;
 int res;

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    const char *fn;
    printf("* wrapping open\n");
    next_func=dlsym(RTLD_NEXT,"open");
    if ((msg=dlerror())!=NULL)
       printf("* dlopen failed : %s\n", msg);
    fn=getenv("KIAUTO_INTERPOSER_LOWLEVEL_IO");
    if ((fn==NULL || !fn[0]) && !FORCE_LOW_LEVEL_LOG)
       printf("* Not logging low level I/O\n");
    else
       do_log=1;
   }

 res=next_func(pathname, flags, mode);

 if (do_log)
   {
    printf("IO:open:%s\n", pathname);
    if (ALL_OPEN_MODES)
       printf("IO:open:0x%X\n", mode);
    fflush(stdout);
   }
 return res;
}


int close(int fd)
{
 static int(*next_func)(int)=NULL;
 static int do_log=FORCE_LOW_LEVEL_LOG;
 int res;
 char path[1024];
 char result[1024];

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    const char *fn;
    printf("* wrapping close\n");
    next_func=dlsym(RTLD_NEXT,"close");
    if ((msg=dlerror())!=NULL)
       printf("* dlopen failed : %s\n", msg);
    fn=getenv("KIAUTO_INTERPOSER_LOWLEVEL_IO");
    if ((fn==NULL || !fn[0]) && !FORCE_LOW_LEVEL_LOG)
       printf("* Not logging low level I/O\n");
    else
       do_log=1;
   }

 if (do_log)
   {/* Read out the link to our file descriptor. */
    sprintf(path, "/proc/self/fd/%d", fd);
    memset(result, 0, 1024);
    readlink(path, result, 1023);
   }

 res=next_func(fd);
 if (do_log)
   {
    printf("IO:close:%s\n",result);
    fflush(stdout);
   }
 return res;
}


int close64(int fd)
{
 static int(*next_func)(int)=NULL;
 static int do_log=FORCE_LOW_LEVEL_LOG;
 int res;
 char path[1024];
 char result[1024];

 if (next_func==NULL)
   { /* Initialization */
    char *msg;
    const char *fn;
    printf("* wrapping close64\n");
    next_func=dlsym(RTLD_NEXT,"close64");
    if ((msg=dlerror())!=NULL)
       printf("* dlopen failed : %s\n", msg);
    fn=getenv("KIAUTO_INTERPOSER_LOWLEVEL_IO");
    if ((fn==NULL || !fn[0]) && !FORCE_LOW_LEVEL_LOG)
       printf("* Not logging low level I/O\n");
    else
       do_log=1;
   }

 if (do_log)
   {/* Read out the link to our file descriptor. */
    sprintf(path, "/proc/self/fd/%d", fd);
    memset(result, 0, 1024);
    readlink(path, result, 1023);
   }

 res=next_func(fd);
 if (do_log)
   {
    printf("IO:close:%s\n",result);
    fflush(stdout);
   }
 return res;
}
