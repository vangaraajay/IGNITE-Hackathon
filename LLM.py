from openai import OpenAI

class LLMProcessor:
    def __init__(self, api_key, model="gpt-4.1-mini"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate_test_procedure(self, texts):

        prompt = f"""
You are an experienced electrical engineer tasked with creating a test procedure for a LoRa radio PCB. You will be provided with:

- Type of PCB: LoRa Radio
- BOM Documents
- Assembly Testpoint Report / Netlist
- PCB Hardware Specifications
- PCB Software Specifications
- Schematic Files
- Arduino Uno Test Case Files
- Example output file
These files are here: \n\n{'\n\n'.join(texts)}

Your task is to generate a new test case file that in the form of a DOCX document, following these requirements:

1. Strictly follows the format, numbering, headings, and table styles of the example output file.
2. Includes a step-by-step test procedure that an eletrical engineer can follow. In the test procedure:
 - Before powering on UT, verify each power rail is not connected to ground or shorted. Verify each power rail is not connected to another power rail.
 - identify local passive components (resistors, capacitors, inductors) near components that start with "U" (integrated circuits) and "X" (crystals) and include them in the test procedure. Look for easier points to probe, such as test points or vias, and include them in the test procedure.

3. Places special emphasis on voltage guardrail tests:
   - Check power rails at all test points.
   - Specify expected voltages and acceptable tolerances.
   - Include warnings if voltages exceed limits.

4. Covers power-on checks, connectivity tests, functional tests using Arduino test cases, and signal verification.
5. Be concise but detailed enough to perform tests without additional guidance.

Output the result **strictly in the format of the example output file**, including all tables, headings, and numbering.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert test engineer."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

