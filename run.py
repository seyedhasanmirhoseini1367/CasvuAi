"""
Usage:
  python run.py --client acme_hr --goal "Launch a new AI onboarding service"

Client data goes in:  data/clients/<client_id>/  (one .txt file per document)
Competitor data goes in: data/clients/<client_id>/competitors/  (one .txt per competitor)
Output saved to: output/<client_id>_en.md  and  output/<client_id>_fi.md
"""
import argparse
import os
from pipeline import run_pipeline, save_output


def load_txt_files(folder: str) -> list[str]:
    docs = []
    if not os.path.exists(folder):
        return docs
    for fname in os.listdir(folder):
        if fname.endswith(".txt"):
            with open(os.path.join(folder, fname), encoding="utf-8") as f:
                docs.append(f.read())
    return docs


def main():
    parser = argparse.ArgumentParser(description="CasvuAI Content Pipeline")
    parser.add_argument("--client", required=True, help="Client ID (folder name under data/clients/)")
    parser.add_argument("--goal", required=True, help="What content to produce")
    parser.add_argument("--languages", default="English,Finnish", help="Comma-separated target languages")
    args = parser.parse_args()

    client_folder = f"data/clients/{args.client}"
    competitor_folder = f"data/clients/{args.client}/competitors"

    client_docs = load_txt_files(client_folder)
    competitor_docs = load_txt_files(competitor_folder)
    languages = [l.strip() for l in args.languages.split(",")]

    if not client_docs:
        print(f"No .txt files found in {client_folder}/")
        print("Create that folder and add your client's content as .txt files.")
        return

    print(f"Loaded {len(client_docs)} client doc(s), {len(competitor_docs)} competitor doc(s)")

    output = run_pipeline(
        client_id=args.client,
        client_documents=client_docs,
        competitor_documents=competitor_docs,
        goal=args.goal,
        target_languages=languages,
    )

    save_output(output, args.client)


if __name__ == "__main__":
    main()
