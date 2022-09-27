import gradio as gr


class ModelUI():

    def __init__(self):
        self.default_threshold = 0.7

    def make_image_ui(self):
        self.instr_row = gr.Row()
        with self.instr_row:
            self.instr_img = gr.Markdown("""**Step 1**: Please upload an image. To change your input, 
                                        clear the current image and upload a new one""")
        self.img_row = gr.Row()
        with self.img_row:
            self.input_img = gr.Image(label="Input Image")
            self.detect_img = gr.Image(label="Detection Output").style(height=250)

    def make_model_ui(self):
        self.container = gr.Group(visible=False)
        with self.container:
            with gr.Row():
                self.instr_detect = gr.Markdown("""**Step 2**: Please adjust the model parameters if needed and 
                                            click on the Detect Objects button""")
            with gr.Row():
                with gr.Column():
                    with gr.Row(equal_height=True):
                        self.threshold = gr.Slider(0.1, 1, value=self.default_threshold, step=0.05, label="Threshold")
                        self.detect_btn = gr.Button("Detect Objects")
                with gr.Column():
                    self.accordion = gr.Accordion('Model description - Open to learn more', 
                                                open = False)
                    with  self.accordion:
                        self.description = gr.Markdown("""
                        * This model is used for both object detection and segmentation, and can 
                        idetify up to 90 object classes
                        * Parameter(s): Threshold: represents model certainty about the prediction. Lower threshold results
                        in an increase in objects detected (but with a lower confidence score)  
                        """) #todo include list of classes
                


        
    