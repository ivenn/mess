import unittest
from server.messages import DataBuffer


class TestDataBuffer(unittest.TestCase):

    def setUp(self):
        self.data_buffer = DataBuffer()

    def tearUp(self):
        pass

    def test_one_msg_in_one_piece(self):
        piece = b'AAA..'

        dlist = self.data_buffer.push(piece)
        self.assertEqual(b'', self.data_buffer.data_buffer,
                         msg="Buffer should be empty")
        self.assertListEqual(dlist, [b'AAA', ])

    def test_one_msg_in_two_pieces(self):
        piece1 = b'AA'
        piece2 = b'A..'

        dlist = self.data_buffer.push(piece1)
        self.assertListEqual(dlist, [])
        self.assertEqual(b'AA', self.data_buffer.data_buffer,
                         msg="Buffer should contains b'AA'")
        dlist = self.data_buffer.push(piece2)
        self.assertEqual(b'', self.data_buffer.data_buffer,
                         msg="Buffer should be empty")
        self.assertListEqual(dlist, [b'AAA', ])

    def test_one_msg_in_n_pieces(self):
        pieces = [b'A', b'A', b'A', b'.', b'.']

        # push everything except the last piece
        expected = b''
        for num, piece in enumerate(pieces[:-1]):
            dlist = self.data_buffer.push(piece)
            self.assertListEqual(dlist, [])
            expected += piece
            self.assertEqual(expected,
                             self.data_buffer.data_buffer,
                             msg="Buffer should contains {expected}".format(expected=expected))

        # push the last one
        dlist = self.data_buffer.push(pieces[-1])
        self.assertEqual(b'', self.data_buffer.data_buffer,
                         msg="Buffer should be empty")
        self.assertListEqual(dlist, [b'AAA', ])

    def test_two_msg_in_one_piece(self):
        piece = b'AAA..BBBBB..'

        dlist = self.data_buffer.push(piece)
        self.assertEqual(b'', self.data_buffer.data_buffer,
                         msg="Buffer should be empty")
        self.assertListEqual(dlist, [b'AAA', b'BBBBB'])

    def test_n_msg_in_one_piece(self):
        piece = b'AAA..11111..       ..$$$$$..```..'

        dlist = self.data_buffer.push(piece)
        self.assertEqual(b'', self.data_buffer.data_buffer,
                         msg="Buffer should be empty")
        self.assertListEqual(dlist, [b'AAA', b'11111', b'       ', b'$$$$$', b'```'])

    def test_n_msg_in_n_pieces(self):
        # Kind of real life user interaction
        pieces = [b'Hel', b'lo.', b'.',
                  b'world..',
                  b'w', b'e', b'.', b'.',
                  b'love..unittests..',
                  b'!..']

        # list of tuples with expected results(buffer value, list of returned messages)
        expected = [(b'Hel', []),
                    (b'Hello.', []),
                    (b'', [b'Hello']),
                    (b'', [b'world']),
                    (b'w', []),
                    (b'we', []),
                    (b'we.', []),
                    (b'', [b'we']),
                    (b'', [b'love', b'unittests']),
                    (b'', [b'!']), ]

        for piece, exp in zip(pieces, expected):
            dlist = self.data_buffer.push(piece)
            self.assertEqual(exp[0],
                             self.data_buffer.data_buffer,
                             msg="Buffer should contains {expected}".format(expected=exp))
            self.assertListEqual(dlist, exp[1])

    def test_only_single_new_line_symbol_in_piece(self):
        #  new line symbol as a single symbol in piece should be ignored
        piece = b'\n'
        for i in range(5):
            dlist = self.data_buffer.push(piece)
            self.assertEqual(b'', self.data_buffer.data_buffer,
                             msg="Buffer should be empty")
            self.assertListEqual(dlist, [])

    def test_new_line_symbols_with_other_symbols_in_piece(self):
        # new line symbol as one of the symbols in piece should not be ignored
        pieces_and_results = [(b' \n', b' \n', []),
                              (b'a\na', b'a\na', []),
                              (b'\n\n', b'\n\n', []),
                              (b'\n..', b'', [b'\n']),
                              (b'AAA\n..', b'', [b'AAA\n'])]
        for piece, exp_buf, exp_mlist in pieces_and_results:
            dlist = self.data_buffer.push(piece)
            self.assertEqual(exp_buf,
                             self.data_buffer.data_buffer,
                             msg="Buffer should contains {expected}".format(expected=exp_buf))
            self.assertListEqual(dlist, exp_mlist)
            self.data_buffer.flush()


if __name__ == '__main__':
    unittest.main()
