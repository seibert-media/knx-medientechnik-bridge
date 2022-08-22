from mux_handler_zeevee import map_connections


class TestMapConnections:
    def test_empty_list(self):
        result = map_connections([])
        assert result == dict()

    def test_mapping(self):
        result = map_connections([
            'encoder.EventSpaceAppleTv.hdmiAudio; EncoderIN, EventSpaceConfidenceScreen',
            'encoder.EventSpaceAppleTv.video; EncoderIN, EventSpaceConfidenceScreen',
            'encoder.EventSpaceChromeCast.hdmiAudio; EventSpaceRegieDisplay, EventSpaceBeamer',
            'encoder.EventSpaceChromeCast.video; EventSpaceRegieDisplay, EventSpaceBeamer',
            'encoder.InfoBeamerKueche.hdmiAudio; KuecheDisplay, EmpfangDisplayRechts, EmpfangDisplayLinks',
            'encoder.InfoBeamerKueche.video; KuecheDisplay, EmpfangDisplayRechts, EmpfangDisplayLinks',
        ])
        assert result == {
            'EncoderIN': 'EventSpaceAppleTv',
            'EventSpaceConfidenceScreen': 'EventSpaceAppleTv',
            'EventSpaceRegieDisplay': 'EventSpaceChromeCast',
            'EventSpaceBeamer': 'EventSpaceChromeCast',
            'KuecheDisplay': 'InfoBeamerKueche',
            'EmpfangDisplayLinks': 'InfoBeamerKueche',
            'EmpfangDisplayRechts': 'InfoBeamerKueche',
        }
