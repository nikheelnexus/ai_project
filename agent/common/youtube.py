from youtube_transcript_api import YouTubeTranscriptApi
import json
import os
from datetime import datetime
from company_ai_project_old import testrun
from agent.agents import company_agent_template, text_util_agent, company_agent


class YouTubeTranscriptDownloader:
    def __init__(self, save_dir=None):
        """
        Initialize the downloader

        Args:
            save_dir: Directory to save transcripts.
                     If None, uses testrun module directory.
        """
        self.api = YouTubeTranscriptApi()

        if save_dir:
            self.save_dir = save_dir
        else:
            # Get the directory where testrun module is located
            self.save_dir = os.path.dirname(os.path.abspath(testrun.__file__))

        # Create save directory if it doesn't exist
        os.makedirs(self.save_dir, exist_ok=True)

        print(f"📁 Transcripts will be saved in: {self.save_dir}")

    def extract_video_id(self, video_input):
        """Extract video ID from various URL formats"""
        if "youtube.com/watch?v=" in video_input:
            return video_input.split("v=")[1].split("&")[0]
        elif "youtu.be/" in video_input:
            return video_input.split("youtu.be/")[1].split("?")[0]
        return video_input  # Already an ID

    def get_all_available_languages(self, video_id):
        """Get all available transcript languages for a video"""
        try:
            transcript_list = self.api.list(video_id)
            languages = []

            for transcript in transcript_list:
                language_info = {
                    'code': transcript.language_code,
                    'name': transcript.language,
                    'is_generated': transcript.is_generated,
                    'is_translatable': hasattr(transcript, 'translation_languages') and transcript.translation_languages
                }

                if language_info['is_translatable']:
                    language_info['translatable_to'] = [
                        {'code': lang['language_code'], 'name': lang['language']}
                        for lang in transcript.translation_languages
                    ]

                languages.append(language_info)

            return languages

        except Exception as e:
            print(f"Error getting languages: {e}")
            return []

    def get_transcript(self, video_input, language=None):
        """
        Get transcript in any language

        Args:
            video_input: URL or video ID
            language: Language code (e.g., 'en', 'hi'). If None, gets first available.

        Returns:
            (transcript_text, language_code, video_id) or (None, None, None) if failed
        """
        video_id = self.extract_video_id(video_input)
        print(f"📹 Video ID: {video_id}")

        try:
            # Get available languages
            available_langs = self.get_all_available_languages(video_id)

            if not available_langs:
                print("❌ No transcripts available for this video")
                return None, None, video_id

            print(f"\n🌍 Available transcripts:")
            for i, lang in enumerate(available_langs):
                type_str = "auto-generated" if lang['is_generated'] else "manual"
                print(f"  {i + 1}. {lang['name']} ({lang['code']}) - {type_str}")
                if lang.get('translatable_to'):
                    print(f"     Can translate to: {[t['name'] for t in lang['translatable_to']]}")

            # If language specified, try to get it
            if language:
                print(f"\n🔍 Looking for {language} transcript...")

                # Try direct fetch first
                try:
                    transcript = self.api.fetch(video_id, languages=[language])
                    text = " ".join([snippet.text for snippet in transcript])
                    print(f"✅ Direct {language} transcript found")
                    return text, language, video_id
                except:
                    print(f"  ⚠️  No direct {language} transcript")

                    # Check if we can translate to this language
                    for lang_info in available_langs:
                        if lang_info.get('translatable_to'):
                            for translatable_lang in lang_info['translatable_to']:
                                if translatable_lang['code'] == language:
                                    print(f"  🔄 Translating from {lang_info['code']} to {language}...")
                                    try:
                                        # Get the source transcript
                                        source_transcript = self.api.fetch(video_id, languages=[lang_info['code']])
                                        source_text = " ".join([snippet.text for snippet in source_transcript])

                                        # For now, we just get the source since translation needs additional setup
                                        print(
                                            f"  ⚠️  Note: Got {lang_info['code']} transcript. For translation, use Google Translate API.")
                                        return source_text, lang_info['code'], video_id
                                    except Exception as e:
                                        print(f"  ❌ Translation failed: {e}")

            # If no language specified or language not found, get first available
            print(f"\n📥 Getting first available transcript...")
            first_lang = available_langs[0]

            try:
                transcript = self.api.fetch(video_id, languages=[first_lang['code']])
                text = " ".join([snippet.text for snippet in transcript])
                print(f"✅ Using {first_lang['name']} ({first_lang['code']}) transcript")
                return text, first_lang['code'], video_id
            except:
                print(f"❌ Failed to fetch {first_lang['code']} transcript")
                return None, None, video_id

        except Exception as e:
            print(f"❌ Error: {e}")
            return None, None, video_id

    def save_transcript(self, video_input, output_file=None, language=None, format='txt'):
        """
        Save transcript to file in testrun directory

        Args:
            video_input: URL or video ID
            output_file: Output filename (optional)
            language: Language code (optional)
            format: 'txt' or 'json'

        Returns:
            (success, file_path, transcript_data)
        """
        # Get transcript
        transcript_text, lang_code, video_id = self.get_transcript(video_input, language)

        if not transcript_text:
            print("❌ No transcript to save")
            return False, None, None

        # Generate filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if format == 'txt':
                output_file = f"transcript_{video_id}_{lang_code}_{timestamp}.txt"
            else:
                output_file = f"transcript_{video_id}_{lang_code}_{timestamp}.json"

        # Create full path
        file_path = os.path.join(self.save_dir, output_file)

        # Save in requested format
        if format == 'txt':
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(transcript_text)
                print(f"💾 Saved to: {file_path}")
                return True, file_path, transcript_text
            except Exception as e:
                print(f"❌ Error saving TXT: {e}")
                return False, None, None

        elif format == 'json':
            try:
                # Get full transcript data with timestamps
                transcript_data = self.api.fetch(video_id, languages=[lang_code])
                json_data = []
                for snippet in transcript_data:
                    json_data.append({
                        'text': snippet.text,
                        'start': snippet.start,
                        'duration': snippet.duration,
                        'language': lang_code
                    })

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                print(f"💾 Saved to: {file_path}")
                return True, file_path, json_data
            except Exception as e:
                print(f"❌ Error saving JSON: {e}")
                return False, None, None

    def list_transcripts(self):
        """List all transcript files in the save directory"""
        if not os.path.exists(self.save_dir):
            print(f"📁 Directory does not exist: {self.save_dir}")
            return []

        transcript_files = []
        for file in os.listdir(self.save_dir):
            if file.startswith('transcript_') and (file.endswith('.txt') or file.endswith('.json')):
                file_path = os.path.join(self.save_dir, file)
                file_size = os.path.getsize(file_path)
                transcript_files.append({
                    'name': file,
                    'path': file_path,
                    'size': file_size
                })

        return transcript_files

    def run_testrun_on_transcript(self, transcript_file):
        """
        Run testrun module on a transcript file

        Args:
            transcript_file: Path to transcript file or just filename in save_dir

        Returns:
            Result from testrun
        """
        # If just filename is provided, make it a full path
        if not os.path.isabs(transcript_file):
            transcript_file = os.path.join(self.save_dir, transcript_file)

        if not os.path.exists(transcript_file):
            print(f"❌ File not found: {transcript_file}")
            return None

        print(f"\n🚀 Running testrun on: {transcript_file}")

        try:
            # Read the transcript
            with open(transcript_file, 'r', encoding='utf-8') as f:
                transcript_content = f.read()

            # Run testrun on the transcript content
            # Assuming testrun has a main function or process function
            result = testrun.process(transcript_content)  # Adjust based on your testrun API

            print(f"✅ testrun completed successfully")
            return result

        except Exception as e:
            print(f"❌ Error running testrun: {e}")
            import traceback
            traceback.print_exc()
            return None


# Main execution
if __name__ == "__main__":
    print("=" * 60)
    print("YouTube Transcript Downloader")
    print(f"Using testrun directory: {os.path.dirname(os.path.abspath(testrun.__file__))}")
    print("=" * 60)

    # Initialize downloader - will save in testrun directory
    downloader = YouTubeTranscriptDownloader()

    # Test videos
    test_videos = [
        {
            "name": "Hindi only video",
            "url": "https://www.youtube.com/watch?v=vxIXVmQvinI&t=3504s",
            "language": None  # Auto-detect
        }
    ]

    # Option 1: Download new transcript and process
    download_new = True  # Set to False if you already have transcripts

    if download_new:
        for test in test_videos:
            print(f"\n{'=' * 50}")
            print(f"Test: {test['name']}")
            print(f"URL: {test['url']}")

            # Get and save transcript
            success, file_path, transcript_data = downloader.save_transcript(
                video_input=test['url'],
                language=test['language'],
                format='txt'
            )

            if success:
                print(f"\n✅ Transcript saved: {os.path.basename(file_path)}")

                # Optionally run testrun immediately
                run_now = True  # Set to True to run testrun after download
                if run_now:
                    downloader.run_testrun_on_transcript(file_path)

    # Option 2: List existing transcripts and run testrun on them
    print(f"\n{'=' * 50}")
    print("📋 Existing Transcripts:")
    transcript_files = downloader.list_transcripts()

    if transcript_files:
        for i, file_info in enumerate(transcript_files):
            size_kb = file_info['size'] / 1024
            print(f"{i + 1}. {file_info['name']} ({size_kb:.1f} KB)")

        # Ask user which transcript to process
        choice = input(
            f"\nSelect transcript to process (1-{len(transcript_files)}), or 'a' for all, or 'n' for none: ").strip().lower()

        if choice == 'a':
            # Process all transcripts
            for file_info in transcript_files:
                downloader.run_testrun_on_transcript(file_info['path'])
        elif choice.isdigit() and 1 <= int(choice) <= len(transcript_files):
            # Process selected transcript
            selected_file = transcript_files[int(choice) - 1]
            downloader.run_testrun_on_transcript(selected_file['path'])
        elif choice == 'n':
            print("Skipping transcript processing.")
        else:
            print("Invalid choice.")
    else:
        print("No transcript files found.")

    # Option 3: Manual file input
    print(f"\n{'=' * 50}")
    manual_file = input("Or enter path to a specific transcript file (press Enter to skip): ").strip()

    if manual_file:
        if os.path.exists(manual_file):
            downloader.run_testrun_on_transcript(manual_file)
        else:
            print(f"File not found: {manual_file}")

    print(f"\n{'=' * 60}")
    print("🎯 All operations completed!")
    print(f"📁 Files are in: {downloader.save_dir}")

    # Show what's in the directory
    print("\n📋 Directory contents:")
    try:
        files = os.listdir(downloader.save_dir)
        for file in sorted(files):
            if file.endswith(('.txt', '.json', '.py')):
                file_path = os.path.join(downloader.save_dir, file)
                size = os.path.getsize(file_path) / 1024
                print(f"  - {file} ({size:.1f} KB)")
    except Exception as e:
        print(f"  Error listing directory: {e}")