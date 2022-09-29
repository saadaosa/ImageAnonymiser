import gradio as gr


class AnonymiserUI():
    def __init__(self, default_classes):
        self.default_classes = default_classes
        self.default_intensity_ui = 0.2
        self.min_intensity = 1
        self.max_intensity = 57

    def make_anonymiser_ui(self):
        self.container = gr.Group(visible=False)
        with self.container:
            with gr.Row():
                self.instr_anonym = gr.Markdown("""**Step 3**: Please change the anonymisation parameters to update the output""")
            with gr.Row():
                with gr.Column():
                    with gr.Row(equal_height=True):
                        with gr.Column(scale=5):
                            self.target = gr.CheckboxGroup(choices=[], label="Choose the target")
                        with gr.Column(scale=1):
                            self.type = gr.Dropdown(choices=["None"], label="Blur type", value="None")
                    with gr.Row():
                        self.intensity = gr.Slider(0,1, value=self.default_intensity_ui, step=0.05, interactive=True, 
                                            label="Blur Intensity") 
                    with gr.Row():
                        self.accordion = gr.Accordion('Anonymisation description - Open to learn more', 
                                                open = False)
                        with  self.accordion:
                            self.description = gr.Markdown("""
                            * Choose the target: The list of available object classes to anonymise is based on the output of the
                            detection model
                            * Blur type: This can be Box or Mask depending on the detection model. Box allows you to add a 
                            rectangular blur around the object. Mask adds a blur to the target pixels only
                            * Blur intensity: Value from 0 to 1 that allows you to control the level of blur  
                            """)
                    with gr.Row():
                        self.anonymise_btn = gr.Button("Anonymize")
                with gr.Column():    
                    self.anonymise_image = gr.Image(label="Image Anonymised").style(height=300)
                

    def convert_intensity(self, intensity):
        result = int(intensity * (self.max_intensity - self.min_intensity + 1))
        if result % 2 == 0: result+=1 
        return result