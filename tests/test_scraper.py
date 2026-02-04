import unittest
import sys
import os
from unittest.mock import Mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scraper import is_valid, extract_next_links


class TestIsValid(unittest.TestCase):
    # allowed domains

    def test_valid_ics_uci_edu(self):
        self.assertTrue(is_valid("https://ics.uci.edu"))
        self.assertTrue(is_valid("https://www.ics.uci.edu"))
        self.assertTrue(is_valid("https://www.ics.uci.edu/about"))
        self.assertTrue(is_valid("https://www.ics.uci.edu/~faculty/index.html"))
        
    def test_valid_cs_uci_edu(self):
        self.assertTrue(is_valid("https://cs.uci.edu"))
        self.assertTrue(is_valid("https://www.cs.uci.edu"))
        self.assertTrue(is_valid("https://www.cs.uci.edu/about"))
        
    def test_valid_informatics_uci_edu(self):
        self.assertTrue(is_valid("https://informatics.uci.edu"))
        self.assertTrue(is_valid("https://www.informatics.uci.edu"))
        self.assertTrue(is_valid("https://www.informatics.uci.edu/research"))
        
    def test_valid_stat_uci_edu(self):
        self.assertTrue(is_valid("https://stat.uci.edu"))
        self.assertTrue(is_valid("https://www.stat.uci.edu"))
        self.assertTrue(is_valid("https://www.stat.uci.edu/faculty"))
        
    # disallowed domains
    def test_invalid_other_uci_domains(self):
        self.assertFalse(is_valid("https://uci.edu"))
        self.assertFalse(is_valid("https://www.uci.edu"))
        self.assertFalse(is_valid("https://engineering.uci.edu"))
        self.assertFalse(is_valid("https://math.uci.edu"))
        
    def test_invalid_non_uci_domains(self):
        self.assertFalse(is_valid("https://google.com"))
        self.assertFalse(is_valid("https://github.com"))
        self.assertFalse(is_valid("https://example.com"))
        
    def test_invalid_schemes(self):
        self.assertFalse(is_valid("ftp://ics.uci.edu"))
        self.assertFalse(is_valid("file://ics.uci.edu"))
        self.assertFalse(is_valid("mailto:test@ics.uci.edu"))
        
    def test_valid_http_and_https(self):
        self.assertTrue(is_valid("http://ics.uci.edu"))
        self.assertTrue(is_valid("https://ics.uci.edu"))
        
    def test_valid_html_files(self):
        self.assertTrue(is_valid("https://ics.uci.edu/page.html"))
        self.assertTrue(is_valid("https://ics.uci.edu/page.htm"))
        
    def test_valid_urls_without_extensions(self):
        self.assertTrue(is_valid("https://ics.uci.edu"))
        self.assertTrue(is_valid("https://ics.uci.edu/about"))
        self.assertTrue(is_valid("https://ics.uci.edu/faculty/profile"))
        
    def test_invalid_image_files(self):
        self.assertFalse(is_valid("https://ics.uci.edu/image.jpg"))
        self.assertFalse(is_valid("https://ics.uci.edu/image.jpeg"))
        self.assertFalse(is_valid("https://ics.uci.edu/image.png"))
        self.assertFalse(is_valid("https://ics.uci.edu/image.gif"))
        self.assertFalse(is_valid("https://ics.uci.edu/image.bmp"))
        
    def test_invalid_document_files(self):
        self.assertFalse(is_valid("https://ics.uci.edu/document.pdf"))
        self.assertFalse(is_valid("https://ics.uci.edu/document.doc"))
        self.assertFalse(is_valid("https://ics.uci.edu/document.docx"))
        self.assertFalse(is_valid("https://ics.uci.edu/document.ppt"))
        self.assertFalse(is_valid("https://ics.uci.edu/document.pptx"))
        self.assertFalse(is_valid("https://ics.uci.edu/spreadsheet.xls"))
        self.assertFalse(is_valid("https://ics.uci.edu/spreadsheet.xlsx"))
        
    def test_invalid_archive_files(self):
        self.assertFalse(is_valid("https://ics.uci.edu/file.zip"))
        self.assertFalse(is_valid("https://ics.uci.edu/file.rar"))
        self.assertFalse(is_valid("https://ics.uci.edu/file.gz"))
        self.assertFalse(is_valid("https://ics.uci.edu/file.tar"))
        self.assertFalse(is_valid("https://ics.uci.edu/file.7z"))
        
    def test_invalid_media_files(self):
        self.assertFalse(is_valid("https://ics.uci.edu/video.mp4"))
        self.assertFalse(is_valid("https://ics.uci.edu/audio.mp3"))
        self.assertFalse(is_valid("https://ics.uci.edu/video.avi"))
        self.assertFalse(is_valid("https://ics.uci.edu/video.mov"))
        
    def test_invalid_web_assets(self):
        self.assertFalse(is_valid("https://ics.uci.edu/style.css"))
        self.assertFalse(is_valid("https://ics.uci.edu/script.js"))
        
    def test_invalid_data_files(self):
        self.assertFalse(is_valid("https://ics.uci.edu/data.csv"))
        self.assertFalse(is_valid("https://ics.uci.edu/data.dat"))
        self.assertFalse(is_valid("https://ics.uci.edu/data.json"))
        
    # case sensitivity
    def test_case_insensitive_domains(self):
        self.assertTrue(is_valid("https://ICS.UCI.EDU"))
        self.assertTrue(is_valid("https://Ics.Uci.Edu"))
        self.assertTrue(is_valid("https://CS.UCI.EDU/about"))
        
    def test_case_insensitive_extensions(self):
        self.assertFalse(is_valid("https://ics.uci.edu/file.PDF"))
        self.assertFalse(is_valid("https://ics.uci.edu/file.JPG"))
        self.assertTrue(is_valid("https://ics.uci.edu/page.HTML"))
        
    # edge cases 
    def test_subdomain_variations(self):
        self.assertTrue(is_valid("https://archive.ics.uci.edu"))
        self.assertTrue(is_valid("https://vision.ics.uci.edu"))
        self.assertTrue(is_valid("https://kb.ics.uci.edu"))
        
    def test_urls_with_query_parameters(self):
        self.assertTrue(is_valid("https://ics.uci.edu/search?q=test"))
        self.assertTrue(is_valid("https://ics.uci.edu/page.html?id=123"))
        
    def test_urls_with_fragments(self):
        self.assertTrue(is_valid("https://ics.uci.edu/page#section"))
        self.assertTrue(is_valid("https://ics.uci.edu/page.html#top"))

class TestExtractNextLinks(unittest.TestCase):
    
    def create_mock_response(self, url, status, content):
        resp = Mock()
        resp.url = url
        resp.status = status
        resp.raw_response = Mock()
        resp.raw_response.url = url
        resp.raw_response.content = content
        return resp
    
    def test_extract_from_simple_html(self):
        html = b'''
        <html>
            <body>
                <a href="https://ics.uci.edu/page1">Link 1</a>
                <a href="https://cs.uci.edu/page2">Link 2</a>
            </body>
        </html>
        '''
        resp = self.create_mock_response("https://ics.uci.edu", 200, html)
        links = extract_next_links("https://ics.uci.edu", resp, min_text_length=1)
        
        self.assertIn("https://ics.uci.edu/page1", links)
        self.assertIn("https://cs.uci.edu/page2", links)
        self.assertEqual(len(links), 2)
    
    def test_extract_relative_urls(self):
        html = b'''
        <html>
            <body>
                <a href="/about">About</a>
                <a href="contact.html">Contact</a>
                <a href="../parent">Parent</a>
            </body>
        </html>
        '''
        resp = self.create_mock_response("https://ics.uci.edu/dir/page", 200, html)
        links = extract_next_links("https://ics.uci.edu/dir/page", resp, min_text_length=1)
        
        self.assertIn("https://ics.uci.edu/about", links)
        self.assertIn("https://ics.uci.edu/dir/contact.html", links)
        self.assertIn("https://ics.uci.edu/parent", links)
    
    def test_remove_fragments(self):
        html = b'''
        <html>
            <body>
                <a href="https://ics.uci.edu/page#section1">Link 1</a>
                <a href="https://ics.uci.edu/page#section2">Link 2</a>
                <a href="/about#top">Link 3</a>
            </body>
        </html>
        '''
        resp = self.create_mock_response("https://ics.uci.edu", 200, html)
        links = extract_next_links("https://ics.uci.edu", resp, min_text_length=1)
        
        self.assertIn("https://ics.uci.edu/page", links)
        self.assertIn("https://ics.uci.edu/about", links)
        self.assertEqual(len(links), 2)
    
    def test_duplicate_links_removed(self):
        html = b'''
        <html>
            <body>
                <a href="https://ics.uci.edu/page1">Link 1</a>
                <a href="https://ics.uci.edu/page1">Link 1 Again</a>
                <a href="https://ics.uci.edu/page1">Link 1 Third Time</a>
            </body>
        </html>
        '''
        resp = self.create_mock_response("https://ics.uci.edu", 200, html)
        links = extract_next_links("https://ics.uci.edu", resp, min_text_length=1)
        
        self.assertEqual(len(links), 1)
        self.assertIn("https://ics.uci.edu/page1", links)
    
    def test_non_200_status(self):
        html = b'<html><body><a href="https://ics.uci.edu/page1">Link</a></body></html>'
        
        for status in [404, 500, 301, 302, 403]:
            resp = self.create_mock_response("https://ics.uci.edu", status, html)
            links = extract_next_links("https://ics.uci.edu", resp, min_text_length=1)
            self.assertEqual(links, [], f"Expected empty list for status {status}")
    
    def test_no_raw_response(self):
        resp = Mock()
        resp.url = "https://ics.uci.edu"
        resp.status = 200
        resp.raw_response = None
        
        links = extract_next_links("https://ics.uci.edu", resp, min_text_length=1)
        self.assertEqual(links, [])
    
    def test_no_content(self):
        resp = Mock()
        resp.url = "https://ics.uci.edu"
        resp.status = 200
        resp.raw_response = Mock()
        resp.raw_response.content = None
        
        links = extract_next_links("https://ics.uci.edu", resp, min_text_length=1)
        self.assertEqual(links, [])
    
    def test_empty_content(self):
        html = b''
        resp = self.create_mock_response("https://ics.uci.edu", 200, html)
        links = extract_next_links("https://ics.uci.edu", resp, min_text_length=1)
        
        self.assertEqual(links, [])
    
    def test_no_links_in_html(self):
        html = b'<html><body><p>No links here</p></body></html>'
        resp = self.create_mock_response("https://ics.uci.edu", 200, html)
        links = extract_next_links("https://ics.uci.edu", resp, min_text_length=1)
        
        self.assertEqual(links, [])
    
    def test_cross_domain_links(self):
        html = b'''
        <html>
            <head>
                <title>Test Page</title>
                <meta name="description" content="Test description">
            </head>
            <body>
                <a href="https://ics.uci.edu/page1">ICS Page</a>
                <a href="https://google.com">Google</a>
                <a href="https://github.com">GitHub</a>
            </body>
        </html>
        '''
        resp = self.create_mock_response("https://ics.uci.edu", 200, html)
        links = extract_next_links("https://ics.uci.edu", resp, min_text_length=1)
        
        self.assertEqual(len(links), 3)
        self.assertIn("https://ics.uci.edu/page1", links)
        self.assertIn("https://google.com", links)
        self.assertIn("https://github.com", links)
    
    def test_links_with_query_parameters(self):
        html = b'''
        <html>
            <head>
                <title>Test Page</title>
                <meta name="description" content="Test description">
            </head>
            <body>
                <a href="https://ics.uci.edu/search?q=test">Search</a>
                <a href="/page?id=123&name=test">Page</a>
            </body>
        </html>
        '''
        resp = self.create_mock_response("https://ics.uci.edu", 200, html)
        links = extract_next_links("https://ics.uci.edu", resp, min_text_length=1)
        
        self.assertIn("https://ics.uci.edu/search?q=test", links)
        self.assertIn("https://ics.uci.edu/page?id=123&name=test", links)
    
    def test_malformed_html(self):
        html = b'<html><body><a href="https://ics.uci.edu/page1">Link</a><p>Unclosed paragraph'
        resp = self.create_mock_response("https://ics.uci.edu", 200, html)
        links = extract_next_links("https://ics.uci.edu", resp, min_text_length=1)
    
        self.assertIn("https://ics.uci.edu/page1", links)
    
    def test_javascript_links(self):
        html = b'''
        <html>
            <head>
                <title>Test Page</title>
                <meta name="description" content="Test description">
            </head>
            <body>
                <a href="javascript:void(0)">JS Link</a>
                <a href="https://ics.uci.edu/page1">Valid Link</a>
            </body>
        </html>
        '''
        resp = self.create_mock_response("https://ics.uci.edu", 200, html)
        links = extract_next_links("https://ics.uci.edu", resp, min_text_length=1)
        
        self.assertIn("https://ics.uci.edu/page1", links)



if __name__ == '__main__':
    unittest.main()
