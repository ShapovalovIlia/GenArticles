class Config:
    def __init__(
        self, *, phrases_path: str, output_dir: str, system_prompt_path: str
    ) -> None:
        self.phrases_path = phrases_path
        self.output_dir = output_dir
        self.system_prompt_path = system_prompt_path

        with open(f"{system_prompt_path}") as file:
            self.system_prompt = "\n".join(file.readlines())
