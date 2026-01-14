"""
Google Docs API client for posting productivity reports.
"""

import os
from typing import Optional
import logging
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GoogleDocsClient:
    """Client for posting reports to Google Docs."""

    # Scopes required for Google Docs API
    SCOPES = ['https://www.googleapis.com/auth/documents']

    def __init__(self, credentials_path: str = 'credentials.json',
                 token_path: str = 'token.json'):
        """
        Initialize Google Docs client.

        Args:
            credentials_path: Path to OAuth credentials JSON
            token_path: Path to store/load access token
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds = None
        self.service = None

        logger.info("Google Docs client initialized")

    def authenticate(self) -> bool:
        """
        Authenticate with Google API using OAuth 2.0.

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Load existing token if available
            if os.path.exists(self.token_path):
                self.creds = Credentials.from_authorized_user_file(
                    self.token_path, self.SCOPES
                )
                logger.info("Loaded existing Google API credentials")

            # Refresh or obtain new credentials
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    logger.info("Refreshing expired credentials")
                    self.creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_path):
                        logger.error(f"Credentials file not found: {self.credentials_path}")
                        return False

                    logger.info("Starting OAuth flow for new credentials")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)

                # Save credentials for future use
                with open(self.token_path, 'w') as token:
                    token.write(self.creds.to_json())
                logger.info("Credentials saved successfully")

            # Build service
            self.service = build('docs', 'v1', credentials=self.creds)
            logger.info("Google Docs service initialized")
            return True

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    def append_to_document(self, document_id: str, content: str) -> bool:
        """
        Append content to an existing Google Doc.

        Args:
            document_id: Google Doc ID (from URL)
            content: Text content to append

        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            logger.error("Service not initialized. Call authenticate() first.")
            return False

        try:
            # Get document to find end position
            document = self.service.documents().get(documentId=document_id).execute()
            end_index = document.get('body').get('content')[-1].get('endIndex', 1) - 1

            # Prepare requests for batch update
            requests = [
                {
                    'insertText': {
                        'location': {
                            'index': end_index
                        },
                        'text': '\n\n' + content
                    }
                }
            ]

            # Execute batch update
            self.service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()

            logger.info(f"Successfully appended content to document {document_id}")
            return True

        except HttpError as e:
            logger.error(f"HTTP error appending to document: {e}")
            return False
        except Exception as e:
            logger.error(f"Error appending to document: {e}")
            return False

    def create_new_document(self, title: str, content: str) -> Optional[str]:
        """
        Create a new Google Doc with content.

        Args:
            title: Document title
            content: Initial content

        Returns:
            Document ID if successful, None otherwise
        """
        if not self.service:
            logger.error("Service not initialized. Call authenticate() first.")
            return None

        try:
            # Create document
            document = self.service.documents().create(
                body={'title': title}
            ).execute()

            document_id = document.get('documentId')
            logger.info(f"Created new document: {title} (ID: {document_id})")

            # Add initial content
            requests = [
                {
                    'insertText': {
                        'location': {'index': 1},
                        'text': content
                    }
                }
            ]

            self.service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()

            logger.info(f"Added initial content to document {document_id}")
            return document_id

        except HttpError as e:
            logger.error(f"HTTP error creating document: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating document: {e}")
            return None

    def post_daily_report(self, document_id: str, report_text: str,
                         date_str: Optional[str] = None) -> bool:
        """
        Post daily productivity report to Google Doc.

        Args:
            document_id: Target Google Doc ID
            report_text: Formatted report text
            date_str: Date string (defaults to today)

        Returns:
            True if successful, False otherwise
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')

        logger.info(f"Posting daily report for {date_str} to document {document_id}")

        # Add separator and timestamp
        separator = "\n\n" + "=" * 80 + "\n\n"
        full_content = separator + report_text

        return self.append_to_document(document_id, full_content)

    def get_document_title(self, document_id: str) -> Optional[str]:
        """
        Get the title of a Google Doc.

        Args:
            document_id: Google Doc ID

        Returns:
            Document title if successful, None otherwise
        """
        if not self.service:
            logger.error("Service not initialized. Call authenticate() first.")
            return None

        try:
            document = self.service.documents().get(documentId=document_id).execute()
            title = document.get('title')
            logger.info(f"Retrieved document title: {title}")
            return title

        except HttpError as e:
            logger.error(f"HTTP error getting document title: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting document title: {e}")
            return None

    def test_connection(self, document_id: str) -> bool:
        """
        Test connection to Google Docs API and access to specific document.

        Args:
            document_id: Document ID to test access

        Returns:
            True if connection and access successful, False otherwise
        """
        if not self.authenticate():
            logger.error("Authentication failed")
            return False

        title = self.get_document_title(document_id)
        if title:
            logger.info(f"Connection test successful! Document: {title}")
            return True
        else:
            logger.error("Could not access document")
            return False
